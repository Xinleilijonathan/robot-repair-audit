"""Run Isaac Sim's stock Franka scene and record independent object measurements.

This is an installation/baseline pilot, not the held-out paper experiment.
API reference: NVIDIA Isaac Sim 6.2 manipulation tutorial.
"""
from __future__ import annotations

import argparse
import hashlib
import importlib.metadata
import json
import platform
import time
import sys
from pathlib import Path

parser = argparse.ArgumentParser()
parser.add_argument("--output", type=Path, required=True)
parser.add_argument("--repeats", type=int, default=3)
parser.add_argument("--max-steps", type=int, default=1800)
parser.add_argument("--visible", action="store_true")
parser.add_argument("--scene-manifest", type=Path)
parser.add_argument("--controller-config", type=Path)
args, extra = parser.parse_known_args()
sys.argv = [sys.argv[0]] + extra
args.output.mkdir(parents=True, exist_ok=True)

from isaacsim import SimulationApp

app = SimulationApp({"headless": not args.visible, "width": 640, "height": 480})

import numpy as np
import isaacsim.core.experimental.utils.app as app_utils

app_utils.enable_extension("isaacsim.robot_motion.examples")
from isaacsim.core.simulation_manager import SimulationManager
from isaacsim.core.experimental.utils import transform as transform_utils
from isaacsim.robot_motion.examples.manipulation import PickPlaceTask


def measured_grasp_position(task):
    state = task.scenario.read_robot_state()
    config = task.scenario.robot_config.tool
    sites = state.sites
    position = sites.positions.numpy()[sites.position_names.index(config.controller_frame)]
    orientation = sites.orientations.numpy()[sites.orientation_names.index(config.controller_frame)]
    return transform_utils.transform_local_to_world(
        config.controller_to_grasp_position, position, orientation, device="cpu"
    ).numpy()

metadata = {
    "kind": "stock_controller_pilot",
    "isaacsim": importlib.metadata.version("isaacsim"),
    "platform": platform.platform(),
    "script_sha256": hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
    "physics_dt": 1 / 60,
    "physics_device": "cpu",
    "max_steps": args.max_steps,
    "note": "Repeated stock scene; no claim of model-generated repair or generalization.",
}
scenes = json.loads(args.scene_manifest.read_text()) if args.scene_manifest else [{"id": "stock"}]
overrides = json.loads(args.controller_config.read_text()) if args.controller_config else {}
allowed_overrides = {
    "approach_height": ("_approach_height", 0.05, 0.40),
    "lift_height": ("_lift_height", 0.10, 0.40),
    "position_tolerance": ("_position_tolerance", 0.005, 0.035),
    "grasp_position_tolerance": ("_grasp_position_tolerance", 0.005, 0.035),
    "stability_duration": ("_stability_duration", 0.05, 0.50),
    "gripper_dwell": ("_gripper_dwell", 0.10, 1.00),
}
if set(overrides) - set(allowed_overrides):
    raise ValueError("Unknown controller override; evaluator and low-level control are not editable")
for name, value in overrides.items():
    _, low, high = allowed_overrides[name]
    if not isinstance(value, (int, float)) or not np.isfinite(value) or not low <= value <= high:
        raise ValueError(f"Invalid bounded controller parameter: {name}")
if not isinstance(scenes, list) or not scenes or len({s["id"] for s in scenes}) != len(scenes):
    raise ValueError("Scene manifest must contain unique scene identifiers")
metadata.update({"scenes": scenes, "controller_overrides": overrides})
if overrides:
    metadata["kind"] = "controller_parameter_pilot"
    metadata["note"] = "Exploratory parameter edit; not an independently sampled autonomous repair benchmark."
(args.output / "metadata.json").write_text(json.dumps(metadata, indent=2))
task = None
try:
    task = PickPlaceTask()
    task.setup_scene()
    SimulationManager.setup_simulation(dt=1 / 60, device="cpu")
    SimulationManager.get_physics_scenes()[0].set_enabled_gpu_dynamics(False)
    app_utils.play()
    app_utils.update_app(steps=20)
    task.initialize()
    for name, value in overrides.items():
        attribute = allowed_overrides[name][0]
        if not hasattr(task.controller, attribute):
            raise RuntimeError(f"Installed controller does not expose expected field {attribute}")
        setattr(task.controller, attribute, float(value))
    for repetition in range(args.repeats * len(scenes)):
        scene = scenes[repetition // args.repeats]
        pick = np.asarray(scene.get("pick", [0.5, 0.0, 0.0258]), dtype=np.float32)
        task.pick_positions[0] = pick
        task.place_position = np.asarray(scene.get("place", [0.0, 0.5, 0.0258]), dtype=np.float32)
        task.cubes[0].set_default_state(
            positions=pick.reshape(1, 3),
            orientations=np.asarray([[1.0, 0.0, 0.0, 0.0]], dtype=np.float32),
            linear_velocities=np.zeros((1, 3), dtype=np.float32),
            angular_velocities=np.zeros((1, 3), dtype=np.float32),
        )
        task.reset_robot()
        app_utils.update_app(steps=20)
        task.reset()
        started = time.monotonic()
        trajectory = []
        controller_status = {}
        for step in range(args.max_steps):
            app.update()
            if not app.is_running():
                raise RuntimeError("Simulator closed before rollout ended")
            if app_utils.is_playing():
                task.step(1 / 60)
            position = task.cubes[0].get_world_poses()[0].numpy()[0].tolist()
            controller_status = task.status()
            trajectory.append({"step": step, "cube_position": position,
                               "phase": controller_status.get("phase")})
            if task.is_done or task.failed:
                break
        settle_positions = []
        settle_separations = []
        settle_velocities = []
        settle_orientations = []
        for _ in range(30):
            app.update()
            cube_position = task.cubes[0].get_world_poses()[0].numpy()[0]
            settle_positions.append(cube_position.tolist())
            settle_velocities.append(task.cubes[0].get_velocities()[0].numpy()[0].tolist())
            settle_orientations.append(task.cubes[0].get_world_poses()[1].numpy()[0].tolist())
            settle_separations.append(float(np.linalg.norm(measured_grasp_position(task)-cube_position)))
        goal = np.asarray(task.place_position, dtype=float)
        final_position = np.asarray(settle_positions[-1], dtype=float)
        errors = np.linalg.norm(np.asarray(settle_positions) - goal, axis=1)
        lifted = max(row["cube_position"][2] for row in trajectory) > 0.0758
        # Object-state score is separate from the controller's reported completion.
        released_and_retreated = bool(np.all(np.asarray(settle_separations) > 0.08))
        velocities = np.asarray(settle_velocities)
        linear_speed = np.linalg.norm(velocities[:, :3], axis=1)
        quaternions = np.asarray(settle_orientations)
        quaternions = quaternions / np.linalg.norm(quaternions, axis=1, keepdims=True)
        orientation_drift = 2 * np.arccos(np.clip(np.abs(quaternions @ quaternions[0]), 0, 1))
        stable = bool(np.all(linear_speed < 0.02) and np.all(orientation_drift < 0.05))
        state_score = bool(np.all(np.isfinite(errors)) and np.all(errors <= 0.03)
                           and lifted and released_and_retreated and stable and len(trajectory) < args.max_steps)
        result = {
            "repetition": repetition, "steps": len(trajectory),
            "scene_id": scene["id"], "repeat_within_scene": repetition % args.repeats,
            "controller_overrides": overrides,
            "wall_seconds": time.monotonic() - started,
            "controller_status": controller_status,
            "cube_goal": goal.tolist(), "cube_final": final_position.tolist(),
            "final_error_m": float(np.linalg.norm(final_position-goal)),
            "lift_observed": lifted, "object_state_success": state_score,
            "released_and_retreated": released_and_retreated,
            "stable": stable, "max_settle_linear_speed_m_s": float(max(linear_speed)),
            "max_settle_orientation_drift_rad": float(max(orientation_drift)),
            "final_grasp_cube_separation_m": settle_separations[-1],
            "success_definition": "lift above 0.0758m; cube within 0.03m of goal and grasp-frame separation above 0.08m for final 30 frames",
        }
        (args.output / f"rollout_{repetition:03d}.json").write_text(json.dumps(result, indent=2))
        (args.output / f"trajectory_{repetition:03d}.json").write_text(json.dumps(trajectory))
        print("PILOT_RESULT", json.dumps(result), flush=True)
finally:
    if task is not None:
        task.cleanup()
    app_utils.stop()
    app.close()
