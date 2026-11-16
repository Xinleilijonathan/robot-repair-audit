"""Isaac launch diagnostic, not a research experiment."""
import json
import time
from pathlib import Path

started = time.monotonic()
from isaacsim import SimulationApp

app = SimulationApp({"headless": True, "width": 640, "height": 480})
try:
    for _ in range(10):
        app.update()
    result = {"isaac_startup_ok": True, "elapsed_seconds": time.monotonic()-started,
              "kind": "installation_smoke_test"}
    Path(__file__).with_name("isaac_smoke_result.json").write_text(json.dumps(result, indent=2))
    print("ISAAC_SMOKE_OK", json.dumps(result), flush=True)
finally:
    app.close()
