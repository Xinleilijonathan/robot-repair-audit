import json, math
from pathlib import Path
root = Path(__file__).resolve().parents[1] / 'outputs/robot_repair_study'
scenes = []
for radius in [0.80, 0.85]:
    for angle in [-60, -30, 0, 30, 60]:
        a = math.radians(angle)
        scenes.append({'id': f'r{round(radius*100):02d}_a{angle:+03d}',
            'pick': [round(radius*math.cos(a), 7), round(radius*math.sin(a), 7), 0.0258],
            'place': [0.0, 0.5, 0.0258]})
(root / 'boundary_development_scenes.json').write_text(json.dumps(scenes, indent=2))
# Keep the full inner panel if a boundary failure leads to candidate testing.
inner = json.loads((root / 'radial_development_scenes.json').read_text())
(root / 'combined_development_scenes.json').write_text(json.dumps(inner + scenes, indent=2))
