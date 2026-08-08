#!/usr/bin/env python3
"""Extract charts from Jupyter notebook and save as PNG files."""

import json
import base64
import os

# Load the notebook
notebook_path = "jupyter_notebooks/AAI590_Group_1_Capstone_Project_AI_Driven_Cyber_Threat_Detection_and_Intrusion_Detection_System_(AI_CTIDS).ipynb"
print(f"Loading notebook: {notebook_path}")

with open(notebook_path, 'r', encoding='utf-8') as f:
    notebook = json.load(f)

# Create output directory for charts
os.makedirs("docs/charts", exist_ok=True)

chart_count = 0
chart_info = []

print(f"Scanning {len(notebook['cells'])} cells...")

# Scan through all cells
for cell_idx, cell in enumerate(notebook['cells']):
    if cell['cell_type'] == 'code' and 'outputs' in cell:
        for output_idx, output in enumerate(cell['outputs']):
            # Check for image/png outputs
            if 'data' in output and 'image/png' in output['data']:
                chart_count += 1

                # Extract base64 image data
                img_data = output['data']['image/png']

                # Handle both string and list formats
                if isinstance(img_data, list):
                    img_data = ''.join(img_data)

                # Save to file
                filename = f"chart_{chart_count:03d}.png"
                filepath = f"docs/charts/{filename}"

                # Decode and save
                try:
                    with open(filepath, 'wb') as img_file:
                        img_file.write(base64.b64decode(img_data))
                except Exception as e:
                    print(f"Error saving {filename}: {e}")
                    continue

                # Try to get chart title from preceding text output or markdown
                title = f"Chart {chart_count}"

                # Check previous output for title
                if output_idx > 0:
                    prev_output = cell['outputs'][output_idx - 1]
                    if prev_output.get('output_type') == 'stream' and 'text' in prev_output:
                        text_lines = prev_output['text']
                        if isinstance(text_lines, list) and text_lines:
                            title = text_lines[0].strip()[:100]
                        elif isinstance(text_lines, str):
                            title = text_lines.strip()[:100]

                # Get cell source for context
                cell_source = cell.get('source', [])
                if isinstance(cell_source, list):
                    cell_source = ''.join(cell_source)
                cell_source = cell_source[:200].strip()

                chart_info.append({
                    'id': chart_count,
                    'filename': filename,
                    'filepath': filepath,
                    'cell_index': cell_idx,
                    'title': title,
                    'context': cell_source
                })

                print(f"Extracted {filename}: {title}")

print(f"\n✓ Total charts extracted: {chart_count}")

# Save chart inventory
with open("docs/charts/chart_inventory.json", 'w', encoding='utf-8') as f:
    json.dump(chart_info, f, indent=2, ensure_ascii=False)

print(f"✓ Chart inventory saved to docs/charts/chart_inventory.json")
print(f"✓ Charts saved to docs/charts/")
