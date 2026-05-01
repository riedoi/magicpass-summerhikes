import base64
import os
import re
import xml.etree.ElementTree as ET


REPO_CDN_BASE = "https://cdn.jsdelivr.net/gh/riedoi/magicpass-summerhikes"
SWISSTOPO_APP_BASE = "https://swisstopo.app/u"
GEOADMIN_BASE = "https://map.geo.admin.ch/?bgLayer=ch.swisstopo.pixelkarte-farbe"
TARGET_HEADER = [
    "Wanderung",
    "Distanz",
    "Dauer",
    "Schwierigkeit",
    "Swisstopo",
    "Karte",
    "GPX",
    "Quelle",
]
TARGET_SEPARATOR = ["---", "---:", "---:", "---", "---", "---", "---", "---"]


def split_table_row(line):
    stripped = line.strip()
    if not stripped.startswith("|") or not stripped.endswith("|"):
        return []

    cells = []
    current = ""
    bracket_depth = 0
    paren_depth = 0

    for char in stripped[1:-1]:
        if char == "[":
            bracket_depth += 1
        elif char == "]" and bracket_depth:
            bracket_depth -= 1
        elif char == "(":
            paren_depth += 1
        elif char == ")" and paren_depth:
            paren_depth -= 1

        if char == "|" and bracket_depth == 0 and paren_depth == 0:
            cells.append(current.strip())
            current = ""
        else:
            current += char

    cells.append(current.strip())
    return cells


def table_row(cells):
    return "| " + " | ".join(cells) + " |\n"


def is_separator(line):
    return bool(re.match(r"^\|[\s\-:|]+\|$", line.strip()))


def is_hike_table_header(cells):
    return (
        len(cells) >= 6
        and cells[0] == "Wanderung"
        and "Distanz" in cells
        and "Dauer" in cells
        and "Schwierigkeit" in cells
        and "Quelle" in cells
        and ("GPX" in cells or "Karte" in cells or "Swisstopo" in cells or "Tour" in cells)
    )


def get_cell(cells, header, name, default="offen"):
    try:
        index = header.index(name)
    except ValueError:
        return default
    if index >= len(cells):
        return default
    value = cells[index].strip()
    return value if value else default


def normalize_header_for_row(header, cells):
    normalized = list(header)

    # Older intermediate runs produced:
    # Wanderung | Distanz | Dauer | Schwierigkeit | Tour | Tour | Karte | GPX | Quelle
    # while the data rows only had one Tour cell. Remove the duplicate header cell
    # before reading values, so running this script on that state does not drop Quelle.
    while len(normalized) > len(cells) and normalized.count("Tour") > 1:
        normalized.remove("Tour")

    return normalized


def local_gpx_path_from_cell(cell):
    match = re.search(r"\]\((\.\./gpx/[^)]+\.gpx)\)", cell)
    if match:
        return match.group(1)

    match = re.search(
        r"cdn\.jsdelivr\.net/gh/riedoi/magicpass-summerhikes/(gpx/[^)&]+\.gpx)",
        cell,
    )
    if match:
        return "../" + match.group(1)

    return None


def find_local_gpx_path(cells):
    for cell in cells:
        path = local_gpx_path_from_cell(cell)
        if path:
            return path
    return None


def repo_path_from_local(local_path):
    return local_path.replace("../", "", 1)


def cdn_url_for_local_gpx(local_path):
    return f"{REPO_CDN_BASE}/{repo_path_from_local(local_path)}"


def get_bounds(root):
    for elem in root.iter():
        if elem.tag.endswith("bounds"):
            return (
                float(elem.attrib["minlat"]),
                float(elem.attrib["maxlat"]),
                float(elem.attrib["minlon"]),
                float(elem.attrib["maxlon"]),
            )

    lats = []
    lons = []
    for elem in root.iter():
        if "lat" in elem.attrib and "lon" in elem.attrib:
            lats.append(float(elem.attrib["lat"]))
            lons.append(float(elem.attrib["lon"]))

    if not lats or not lons:
        return None

    return min(lats), max(lats), min(lons), max(lons)


def wgs84_to_lv95(lat, lon):
    lat_aux = (lat * 3600 - 169028.66) / 10000
    lon_aux = (lon * 3600 - 26782.5) / 10000

    east = (
        2600072.37
        + 211455.93 * lon_aux
        - 10938.51 * lon_aux * lat_aux
        - 0.36 * lon_aux * lat_aux**2
        - 44.54 * lon_aux**3
    )
    north = (
        1200147.07
        + 308807.95 * lat_aux
        + 3745.25 * lon_aux**2
        + 76.63 * lat_aux**2
        - 194.56 * lon_aux**2 * lat_aux
        + 119.79 * lat_aux**3
    )

    return east, north


def zoom_for_bounds(minlat, maxlat, minlon, maxlon):
    diff = max(maxlat - minlat, maxlon - minlon)
    if diff > 0.2:
        return 3
    if diff > 0.1:
        return 4
    if diff > 0.05:
        return 5
    if diff > 0.02:
        return 6
    if diff > 0.01:
        return 7
    if diff > 0.005:
        return 8
    return 9


def build_map_cells(markdown_file, local_gpx_path):
    repo_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    abs_gpx_path = os.path.normpath(
        os.path.join(os.path.dirname(markdown_file), local_gpx_path)
    )
    local_gpx_cell = f"[GPX]({local_gpx_path})"
    cdn_url = cdn_url_for_local_gpx(local_gpx_path)

    if not os.path.exists(abs_gpx_path):
        print(f"  Missing GPX file: {os.path.relpath(abs_gpx_path, repo_root)}")
        return "offen", "offen", local_gpx_cell

    try:
        root = ET.parse(abs_gpx_path).getroot()
    except ET.ParseError as error:
        print(f"  Invalid GPX file {os.path.relpath(abs_gpx_path, repo_root)}: {error}")
        return "offen", "offen", local_gpx_cell

    bounds = get_bounds(root)
    if bounds is None:
        print(f"  No coordinates in GPX file: {os.path.relpath(abs_gpx_path, repo_root)}")
        return "offen", "offen", local_gpx_cell

    minlat, maxlat, minlon, maxlon = bounds
    center_lat = (minlat + maxlat) / 2
    center_lon = (minlon + maxlon) / 2
    east, north = wgs84_to_lv95(center_lat, center_lon)
    zoom = zoom_for_bounds(minlat, maxlat, minlon, maxlon)

    swisstopo_payload = base64.b64encode(cdn_url.encode("utf-8")).decode("ascii")
    swisstopo = f"[Tour]({SWISSTOPO_APP_BASE}/{swisstopo_payload})"
    karte = (
        f"[Karte]({GEOADMIN_BASE}&layers=GPX%7C%7C{cdn_url}"
        f"&center={east:.2f},{north:.2f}&z={zoom})"
    )

    return swisstopo, karte, local_gpx_cell


def normalize_data_row(markdown_file, header, cells):
    header = normalize_header_for_row(header, cells)
    base = [
        get_cell(cells, header, "Wanderung"),
        get_cell(cells, header, "Distanz"),
        get_cell(cells, header, "Dauer"),
        get_cell(cells, header, "Schwierigkeit"),
    ]
    quelle = get_cell(cells, header, "Quelle")
    local_gpx_path = find_local_gpx_path(cells)

    if local_gpx_path:
        swisstopo, karte, gpx = build_map_cells(markdown_file, local_gpx_path)
    else:
        swisstopo = "offen"
        karte = "offen"
        gpx = "offen"

    return base + [swisstopo, karte, gpx, quelle]


def process_markdown_file(filepath):
    with open(filepath, "r", encoding="utf-8") as file:
        lines = file.readlines()

    output = []
    in_hike_table = False
    header = []

    for line in lines:
        cells = split_table_row(line)

        if is_hike_table_header(cells):
            output.append(table_row(TARGET_HEADER))
            in_hike_table = True
            header = cells
            continue

        if in_hike_table and is_separator(line):
            output.append(table_row(TARGET_SEPARATOR))
            continue

        if in_hike_table and cells:
            output.append(table_row(normalize_data_row(filepath, header, cells)))
            continue

        in_hike_table = False
        header = []
        output.append(line)

    with open(filepath, "w", encoding="utf-8") as file:
        file.writelines(output)


def main():
    repo_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    dest_dir = os.path.join(repo_root, "destinations")

    for filename in sorted(os.listdir(dest_dir)):
        if filename.endswith(".md"):
            print(f"Processing {filename}...")
            process_markdown_file(os.path.join(dest_dir, filename))

    print("Done.")


if __name__ == "__main__":
    main()
