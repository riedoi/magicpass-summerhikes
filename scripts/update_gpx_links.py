import os
import re
import urllib.request
import json
import xml.etree.ElementTree as ET

def get_lv95(lat, lon):
    url = f"https://geodesy.geo.admin.ch/reframe/wgs84tolv95?easting={lon}&northing={lat}"
    try:
        req = urllib.request.urlopen(url)
        res = json.loads(req.read().decode('utf-8'))
        return res['coordinates'][0], res['coordinates'][1]
    except Exception as e:
        print(f"Error converting coordinates: {e}")
        return 2600000, 1200000 # Default to Bern

def get_zoom(lat_diff, lon_diff):
    diff = max(lat_diff, lon_diff)
    if diff > 0.2: return 3
    if diff > 0.1: return 4
    if diff > 0.05: return 5
    if diff > 0.02: return 6
    if diff > 0.01: return 7
    if diff > 0.005: return 8
    return 9

def get_bounds(root):
    for elem in root.iter():
        if 'bounds' in elem.tag:
            return float(elem.attrib['minlat']), float(elem.attrib['maxlat']), float(elem.attrib['minlon']), float(elem.attrib['maxlon'])
            
    # Calculate from points
    lats = []
    lons = []
    for elem in root.iter():
        if 'lat' in elem.attrib and 'lon' in elem.attrib:
            lats.append(float(elem.attrib['lat']))
            lons.append(float(elem.attrib['lon']))
            
    if lats and lons:
        return min(lats), max(lats), min(lons), max(lons)
        
    return None

def process_markdown_file(filepath):
    with open(filepath, 'r') as f:
        lines = f.readlines()

    out_lines = []
    in_table = False
    gpx_col_index = -1
    
    for i, line in enumerate(lines):
        stripped_line = line.strip()
        if stripped_line.startswith('|') and 'GPX' in stripped_line and 'Quelle' in stripped_line and not in_table:
            # Table header
            cols = [c.strip() for c in stripped_line.split('|')[1:-1]]
            if 'Karte' in cols or 'Karte (Swisstopo)' in cols:
                # Already processed
                out_lines.append(line)
                continue
            
            try:
                gpx_col_index = cols.index('GPX')
            except ValueError:
                out_lines.append(line)
                continue
                
            cols.insert(gpx_col_index + 1, 'Karte')
            out_lines.append('| ' + ' | '.join(cols) + ' |\n')
            in_table = True
        elif stripped_line.startswith('|---') and in_table:
            # Separator
            cols = [c.strip() for c in stripped_line.split('|')[1:-1]]
            cols.insert(gpx_col_index + 1, '---')
            out_lines.append('| ' + ' | '.join(cols) + ' |\n')
        elif stripped_line.startswith('|') and in_table:
            # Data row
            cols = [c.strip() for c in stripped_line.split('|')[1:-1]]
            if len(cols) > gpx_col_index:
                gpx_cell = cols[gpx_col_index]
                # Extract path: [GPX](../gpx/...)
                m = re.search(r'\]\(([^)]+\.gpx)\)', gpx_cell)
                if m:
                    rel_path = m.group(1)
                    clean_path = rel_path.replace('../', '')
                    abs_gpx_path = os.path.join(os.path.dirname(os.path.dirname(filepath)), clean_path)
                    
                    if os.path.exists(abs_gpx_path):
                        # Parse GPX
                        try:
                            tree = ET.parse(abs_gpx_path)
                            root = tree.getroot()
                            bounds = get_bounds(root)
                            
                            if bounds is not None:
                                minlat, maxlat, minlon, maxlon = bounds
                                center_lat = (minlat + maxlat) / 2
                                center_lon = (minlon + maxlon) / 2
                                lat_diff = maxlat - minlat
                                lon_diff = maxlon - minlon
                                
                                E, N = get_lv95(center_lat, center_lon)
                                z = get_zoom(lat_diff, lon_diff)
                                
                                url = f"https://map.geo.admin.ch/?bgLayer=ch.swisstopo.pixelkarte-farbe&layers=GPX||https://cdn.jsdelivr.net/gh/riedoi/magicpass-summerhikes/{clean_path}&center={E:.2f},{N:.2f}&z={z}"
                                karte_cell = f"[Karte]({url})"
                            else:
                                print(f"No points found in {abs_gpx_path}")
                                karte_cell = "keine Karte"
                        except Exception as e:
                            print(f"Failed to parse {abs_gpx_path}: {e}")
                            karte_cell = "keine Karte"
                    else:
                        print(f"File not found: {abs_gpx_path}")
                        karte_cell = "keine Karte"
                else:
                    karte_cell = "-"
                
                cols.insert(gpx_col_index + 1, karte_cell)
                out_lines.append('| ' + ' | '.join(cols) + ' |\n')
            else:
                out_lines.append(line)
                in_table = False # End of table
        else:
            in_table = False
            out_lines.append(line)
            
    with open(filepath, 'w') as f:
        f.writelines(out_lines)

if __name__ == "__main__":
    dest_dir = "/Users/ismosh/Documents/_Projects_&_Software/magicpass_summer/magic-pass-summer-hikes/destinations"
    for filename in os.listdir(dest_dir):
        if filename.endswith(".md"):
            print(f"Processing {filename}...")
            process_markdown_file(os.path.join(dest_dir, filename))
    print("Done!")
