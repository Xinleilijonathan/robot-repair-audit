You are improving a robot controller. Propose ONE parameter edit.
Answer from the information in this message only. Do not use any tools: do not read or write files, run commands or search the web.

## System
NVIDIA Isaac Sim 6.2, Franka Panda arm, the stock pick-and-place example. CPU physics at 60 Hz. One 5 cm cube is picked from a position on the table and placed at a fixed goal (x = 0, y = 0.5 m). Each run has a horizon of 1,800 steps (30 s).

## What you may change
Six scalar parameters of the pick-and-place state machine. Everything else (motion generation, phase timeouts, scenes and scoring) is fixed.

| Parameter | Current value | Allowed range | Meaning |
|---|---|---|---|
| `approach_height` | 0.3 | 0.05 to 0.4 | vertical offset above the pick/place pose used in the APPROACH phases (m) |
| `lift_height` | 0.3 | 0.1 to 0.4 | vertical offset above the pick/place pose used in LIFT and RETREAT (m) |
| `position_tolerance` | 0.015 | 0.005 to 0.035 | tool-position error below which a phase counts as converged (m), all phases except GRASP |
| `grasp_position_tolerance` | 0.015 | 0.005 to 0.035 | the same tolerance used only in GRASP (m); stored separately, so changing position_tolerance does not change it |
| `stability_duration` | 0.1 | 0.05 to 0.5 | time the tool must stay converged before the phase advances (s) |
| `gripper_dwell` | 0.2 | 0.1 to 1 | minimum time spent in GRASP and RELEASE (s) |

## Controller source (the state machine these parameters belong to)
```python
# SPDX-FileCopyrightText: Copyright (c) 2026 NVIDIA CORPORATION & AFFILIATES. All rights reserved.
# SPDX-License-Identifier: Apache-2.0
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
# http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

"""Robot-independent pick-and-place state machine."""

from __future__ import annotations

from collections.abc import Mapping
from enum import Enum, auto

import isaacsim.robot_motion.experimental.motion_generation as mg
import numpy as np
import warp as wp
from isaacsim.core.experimental.utils import transform as transform_utils

from .gripper import JointGripperController, SurfaceGripperController

_Pose = tuple[np.ndarray, np.ndarray]


class PickPlacePhase(Enum):
    """Phase of the pick-and-place state machine."""

    APPROACH_PICK = auto()
    #: Move above the pick pose.
    DESCEND_PICK = auto()
    #: Move to the pick pose.
    GRASP = auto()
    #: Close the gripper at the pick pose.
    LIFT = auto()
    #: Lift the grasped object.
    APPROACH_PLACE = auto()
    #: Move above the place pose.
    DESCEND_PLACE = auto()
    #: Move to the place pose.
    RELEASE = auto()
    #: Open the gripper at the place pose.
    RETREAT = auto()
    #: Move away from the released object.
    DONE = auto()
    #: Complete the pick-and-place sequence.
    FAILED = auto()
    #: Stop the sequence after an error.


_ACTIVE_PHASES = (
    PickPlacePhase.APPROACH_PICK,
    PickPlacePhase.DESCEND_PICK,
    PickPlacePhase.GRASP,
    PickPlacePhase.LIFT,
    PickPlacePhase.APPROACH_PLACE,
    PickPlacePhase.DESCEND_PLACE,
    PickPlacePhase.RELEASE,
    PickPlacePhase.RETREAT,
)

_DEFAULT_TIMEOUTS = {
    PickPlacePhase.APPROACH_PICK: 5.0,
    PickPlacePhase.DESCEND_PICK: 5.0,
    PickPlacePhase.GRASP: 2.0,
    PickPlacePhase.LIFT: 5.0,
    PickPlacePhase.APPROACH_PLACE: 7.0,
    PickPlacePhase.DESCEND_PLACE: 5.0,
    PickPlacePhase.RELEASE: 2.0,
    PickPlacePhase.RETREAT: 5.0,
}


class PickPlaceController(mg.BaseController):
    """State machine that coordinates an arm and gripper for pick-and-place.

    Call :meth:`reset` with named ``pick`` and ``place`` goal sites. The controller
    snapshots those goals, advances after the measured tool pose remains within tolerance,
    and waits for observable gripper completion during grasp and release.

    Args:
        arm_controller: Controller that generates arm commands for a tool-pose target.
        gripper_open_controller: Controller that opens the configured gripper.
        gripper_close_controller: Controller that closes the configured gripper.
        robot_site_space: Ordered names of robot spatial sites.
        tool_frame: Site name controlled by the arm controller.
        controller_to_grasp_position: Translation from the controller frame to the grasp frame.
        controller_to_grasp_orientation: Rotation from the controller frame to the grasp frame.
        grasp_orientation: Grasp orientation used when a goal omits orientation.
        phase_timeouts: Overrides for active-phase timeout durations.
        approach_height: Vertical offset used before descending to a goal.
        lift_height: Vertical offset used while carrying or retreating.
        position_tolerance: Maximum tool-position error for convergence.
        grasp_position_tolerance: Optional position tolerance used only while grasping.
        orientation_tolerance: Maximum tool-orientation error for convergence.
        stability_duration: Time the measured tool pose must remain converged.
        gripper_dwell: Minimum time spent in grasp and release phases.

    Raises:
        ValueError: If the tool frame, tolerances, transforms, or timeouts are invalid.

    Example:

    .. code-block:: python

        >>> controller = PickPlaceController(
        ...     arm_controller=arm_controller,
        ...     gripper_open_controller=open_gripper,
        ...     gripper_close_controller=close_gripper,
        ...     robot_site_space=["tool0"],
        ...     tool_frame="tool0",
        ... )  # doctest: +SKIP
    """

    PICK_SITE = "pick"
    #: Goal site name used for the pick pose.
    PLACE_SITE = "place"
    #: Goal site name used for the place pose.

    def __init__(
        self,
        *,
        arm_controller: mg.BaseController,
        gripper_open_controller: JointGripperController | SurfaceGripperController,
        gripper_close_controller: JointGripperController | SurfaceGripperController,
        robot_site_space: list[str],
        tool_frame: str,
        controller_to_grasp_position: tuple[float, float, float] = (0.0, 0.0, 0.0),
        controller_to_grasp_orientation: tuple[float, float, float, float] = (1.0, 0.0, 0.0, 0.0),
        grasp_orientation: tuple[float, float, float, float] = (0.0, 1.0, 0.0, 0.0),
        phase_timeouts: Mapping[PickPlacePhase, float] | None = None,
        approach_height: float = 0.20,
        lift_height: float = 0.30,
        position_tolerance: float = 0.015,
        grasp_position_tolerance: float | None = None,
        orientation_tolerance: float = 0.12,
        stability_duration: float = 0.10,
        gripper_dwell: float = 0.20,
    ) -> None:
        if tool_frame not in robot_site_space:
            raise ValueError("tool_frame must be present in robot_site_space.")
        scalar_settings = (
            approach_height,
            lift_height,
            stability_duration,
            gripper_dwell,
        )
        if any(not np.isfinite(value) or value < 0.0 for value in scalar_settings):
            raise ValueError("Controller heights and durations must be finite and non-negative.")
        tolerances = (position_tolerance, orientation_tolerance)
        if grasp_position_tolerance is not None:
            tolerances += (grasp_position_tolerance,)
        if any(not np.isfinite(value) or value <= 0.0 for value in tolerances):
            raise ValueError("Controller tolerances must be finite and positive.")

        self._robot_site_space = list(robot_site_space)
        self._tool_frame = tool_frame
        self._controller_to_grasp_position = _validate_position(controller_to_grasp_position)
        self._controller_to_grasp_orientation = _normalize_quaternion(controller_to_grasp_orientation)
        self._default_orientation = _normalize_quaternion(grasp_orientation)
        self._approach_height = float(approach_height)
        self._lift_height = float(lift_height)
        self._position_tolerance = float(position_tolerance)
        self._grasp_position_tolerance = (
            self._position_tolerance if grasp_position_tolerance is None else float(grasp_position_tolerance)
        )
        self._orientation_tolerance = float(orientation_tolerance)
        self._stability_duration = float(stability_duration)
        self._gripper_dwell = float(gripper_dwell)

        self._timeouts = dict(_DEFAULT_TIMEOUTS)
        if phase_timeouts is not None:
            if any(phase not in _ACTIVE_PHASES for phase in phase_timeouts):
                raise ValueError("phase_timeouts may only override active phases.")
            self._timeouts.update(phase_timeouts)
        if any(not np.isfinite(self._timeouts[phase]) or self._timeouts[phase] <= 0.0 for phase in _ACTIVE_PHASES):
            raise ValueError("Every active phase timeout must be finite and positive.")

        open_phases = {
            PickPlacePhase.APPROACH_PICK,
            PickPlacePhase.DESCEND_PICK,
            PickPlacePhase.RELEASE,
            PickPlacePhase.RETREAT,
        }
        self._grippers = {
            phase: gripper_open_controller if phase in open_phases else gripper_close_controller
            for phase in _ACTIVE_PHASES
        }
        self._selector = mg.SelectableController(
            {phase: mg.CombinedController([arm_controller, self._grippers[phase]]) for phase in _ACTIVE_PHASES},
            PickPlacePhase.APPROACH_PICK,
        )

        self._phase = PickPlacePhase.APPROACH_PICK
        self._phase_started = 0.0
        self._stable_since: float | None = None
        self._last_time = 0.0
        self._pick: _Pose | None = None
        self._place: _Pose | None = None
        self._failed_reason: str | None = None

    @property
    def phase(self) -> PickPlacePhase:
        """Get the current state-machine phase.

        Returns:
            Current pick-and-place phase.

        Example:

        .. code-block:: python

            >>> controller.phase  # doctest: +SKIP
            <PickPlacePhase.APPROACH_PICK: 1>
        """
        return self._phase

    @property
    def is_done(self) -> bool:
        """Check whether the sequence completed successfully.

        Returns:
            True if the controller reached the terminal done phase.

        Example:

        .. code-block:: python

            >>> controller.is_done  # doctest: +SKIP
            False
        """
        return self._phase is PickPlacePhase.DONE

    @property
    def failed(self) -> bool:
        """Check whether the sequence stopped after an error.

        Returns:
            True if the controller reached the terminal failed phase.

        Example:

        .. code-block:: python

            >>> controller.failed  # doctest: +SKIP
            False
        """
        return self._phase is PickPlacePhase.FAILED

    @property
    def failure_reason(self) -> str | None:
        """Get the reason for the most recent controller failure.

        Returns:
            Failure description, or None if the controller has not failed.

        Example:

        .. code-block:: python

            >>> controller.failure_reason  # doctest: +SKIP
        """
        return self._failed_reason

    @property
    def phase_timeouts(self) -> Mapping[PickPlacePhase, float]:
        """Get a copy of the configured active-phase timeouts.

        Returns:
            Mapping from each active phase to its timeout duration in seconds.

        Example:

        .. code-block:: python

            >>> controller.phase_timeouts[PickPlacePhase.GRASP]  # doctest: +SKIP
            2.0
        """
        return self._timeouts.copy()

    def reset(
        self, estimated_state: mg.RobotState, setpoint_state: mg.RobotState | None, t: float, **kwargs: object
    ) -> bool:
        """Reset the sequence and snapshot the pick and place goals.

        Args:
            estimated_state: Current robot state containing the measured tool pose.
            setpoint_state: State containing named ``pick`` and ``place`` goal sites.
            t: Current controller time.
            **kwargs: Additional inputs forwarded to child controllers.

        Returns:
            True if the goals and child controllers were reset, False on failure.

        Example:

        .. code-block:: python

            >>> controller.reset(estimated_state, goals, 0.0)  # doctest: +SKIP
            True
        """
        try:
            if not np.isfinite(t):
                raise ValueError("Controller time must be finite.")
            self._controller_pose(estimated_state)
            self._pick = self._read_goal(setpoint_state, self.PICK_SITE)
            self._place = self._read_goal(setpoint_state, self.PLACE_SITE)
            self._phase = PickPlacePhase.APPROACH_PICK
            self._phase_started = float(t)
            self._stable_since = None
            self._last_time = float(t)
            self._failed_reason = None
            if not self._selector.reset(estimated_state, self._make_arm_setpoint(), t, **kwargs):
                raise RuntimeError("Initial controller reset failed.")
        except (RuntimeError, ValueError) as exc:
            self._fail(str(exc))
            return False
        return True

    def forward(
        self, estimated_state: mg.RobotState, setpoint_state: mg.RobotState | None, t: float, **kwargs: object
    ) -> mg.RobotState | None:
        """Advance the state machine and generate the current robot command.

        Args:
            estimated_state: Current robot state containing measured joints and tool pose.
            setpoint_state: Ignored after goals are captured by :meth:`reset`.
            t: Current controller time.
            **kwargs: Additional inputs forwarded to child controllers.

        Returns:
            Desired robot state, or None if the controller fails.

        Example:

        .. code-block:: python

            >>> controller.forward(estimated_state, None, 0.01)  # doctest: +SKIP
        """
        if self.is_done:
            return mg.RobotState()
        if self.failed:
            return None
        try:
            self._validate_time(t)
            measured = self._controller_pose(estimated_state)
            target = self._target()
            desired = self._selector.forward(estimated_state, self._make_arm_setpoint(target), t, **kwargs)
            if desired is None:
                raise RuntimeError(f"Controller composition failed in phase {self._phase.name}.")
            if self._phase_complete(estimated_state, measured, target, t):
                self._advance(t)
            elif t - self._phase_started >= self._timeouts[self._phase]:
                position_error, orientation_error = _pose_errors(measured, target)
                raise RuntimeError(
                    f"{self._phase.name} timed out after {self._timeouts[self._phase]:.3f} s "
                    f"(position error {position_error:.4f} m, orientation error {orientation_error:.4f} rad)."
                )
            self._last_time = float(t)
            return desired
        except (RuntimeError, ValueError) as exc:
            self._fail(str(exc))
            return None

    def _advance(self, t: float) -> None:
        next_index = _ACTIVE_PHASES.index(self._phase) + 1
        if next_index == len(_ACTIVE_PHASES):
            self._phase = PickPlacePhase.DONE
        else:
            self._phase = _ACTIVE_PHASES[next_index]
            self._selector.set_next_controller(self._phase)
        self._phase_started = float(t)
        self._stable_since = None

    def _phase_complete(
        self,
        estimated_state: mg.RobotState,
        measured: _Pose,
        target: _Pose,
        t: float,
    ) -> bool:
        position_error, orientation_error = _pose_errors(measured, target)
        position_tolerance = (
            self._grasp_position_tolerance if self._phase is PickPlacePhase.GRASP else self._position_tolerance
        )
        converged = position_error <= position_tolerance and orientation_error <= self._orientation_tolerance
        if not converged:
            self._stable_since = None
            return False

        if self._stable_since is None:
            self._stable_since = float(t)
        if t - self._stable_since < self._stability_duration:
            return False

        if self._phase in {PickPlacePhase.GRASP, PickPlacePhase.RELEASE}:
            return t - self._phase_started >= self._gripper_dwell and self._grippers[self._phase].is_complete(
                estimated_state
            )
        return True

    def _target(self) -> _Pose:
        if self._pick is None or self._place is None:
            raise RuntimeError("PickPlaceController has not been reset.")
        grasp = (
            self._place
            if self._phase
            in {
                PickPlacePhase.APPROACH_PLACE,
                PickPlacePhase.DESCEND_PLACE,
                PickPlacePhase.RELEASE,
                PickPlacePhase.RETREAT,
            }
            else self._pick
        )

        position = grasp[0].copy()
        if self._phase in {PickPlacePhase.APPROACH_PICK, PickPlacePhase.APPROACH_PLACE}:
            position[2] += self._approach_height
        elif self._phase in {PickPlacePhase.LIFT, PickPlacePhase.RETREAT}:
            position[2] += self._lift_height

        grasp_to_controller_orientation = transform_utils.quaternion_conjugate(
            self._controller_to_grasp_orientation, dtype=wp.float64, device="cpu"
        ).numpy()
        grasp_to_controller_position = transform_utils.rotate_vectors_by_quaternion(
            -self._controller_to_grasp_position,
            grasp_to_controller_orientation,
            dtype=wp.float64,
            device="cpu",
        ).numpy()
        controller_position = transform_utils.transform_local_to_world(
            grasp_to_controller_position,
            position,
            grasp[1],
            dtype=wp.float64,
            device="cpu",
        ).numpy()
        controller_orientation = transform_utils.quaternion_multiplication(
            grasp[1],
            grasp_to_controller_orientation,
            dtype=wp.float64,
            device="cpu",
        ).numpy()
        return controller_position, _normalize_quaternion(controller_orientation)

    def _make_arm_setpoint(self, target: _Pose | None = None) -> mg.RobotState:
        target = self._target() if target is None else target
        return mg.RobotState(
            sites=mg.SpatialState.from_name(
                spatial_space=self._robot_site_space,
                positions=(
                    [self._tool_frame],
                    wp.array([target[0]], dtype=wp.float32, device="cpu"),
                ),
                orientations=(
                    [self._tool_frame],
                    wp.array([target[1]], dtype=wp.float32, device="cpu"),
                ),
            )
        )

    def _read_goal(self, setpoint: mg.RobotState | None, name: str) -> _Pose:
        if setpoint is None or setpoint.sites is None or setpoint.sites.positions is None:
            raise ValueError("PickPlaceController requires named 'pick' and 'place' position sites.")
        sites = setpoint.sites
        if name not in sites.position_names:
            raise ValueError("PickPlaceController requires named 'pick' and 'place' position sites.")
        position = np.asarray(sites.positions.numpy()[sites.position_names.index(name)], dtype=np.float64).copy()
        orientation = self._default_orientation
        if sites.orientations is not None and name in sites.orientation_names:
            orientation = _normalize_quaternion(sites.orientations.numpy()[sites.orientation_names.index(name)])
        return _validate_position(position, label=f"Goal site {name!r}"), orientation

    def _controller_pose(self, state: mg.RobotState) -> _Pose:
        if state.sites is None or state.sites.positions is None or state.sites.orientations is None:
            raise ValueError(f"Estimated RobotState requires measured site {self._tool_frame!r}.")
        sites = state.sites
        if self._tool_frame not in sites.position_names or self._tool_frame not in sites.orientation_names:
            raise ValueError(f"Estimated RobotState requires measured site {self._tool_frame!r}.")
        position = _validate_position(sites.positions.numpy()[sites.position_names.index(self._tool_frame)])
        orientation = _normalize_quaternion(sites.orientations.numpy()[sites.orientation_names.index(self._tool_frame)])
        return position, orientation

    def _validate_time(self, t: float) -> None:
        if not np.isfinite(t):
            raise ValueError("Controller time must be finite.")
        if t < self._last_time:
            raise ValueError("Controller time moved backwards.")

    def _fail(self, reason: str) -> None:
        self._phase = PickPlacePhase.FAILED
        self._failed_reason = reason


def _normalize_quaternion(orientation: tuple[float, ...] | np.ndarray) -> np.ndarray:
    quaternion = np.asarray(orientation, dtype=np.float64)
    norm = np.linalg.norm(quaternion)
    if quaternion.shape != (4,) or not np.isfinite(norm) or norm <= 0.0:
        raise ValueError("Quaternion must be finite and nonzero.")
    return quaternion / norm


def _validate_position(position: tuple[float, ...] | np.ndarray, label: str = "Position") -> np.ndarray:
    position = np.asarray(position, dtype=np.float64)
    if position.shape != (3,) or not np.isfinite(position).all():
        raise ValueError(f"{label} must contain three finite XYZ values.")
    return position.copy()


def _quaternion_distance(lhs: tuple[float, ...], rhs: tuple[float, ...]) -> float:
    dot = abs(float(np.dot(_normalize_quaternion(lhs), _normalize_quaternion(rhs))))
    return 2.0 * float(np.arccos(np.clip(dot, 0.0, 1.0)))


def _pose_errors(measured: _Pose, target: _Pose) -> tuple[float, float]:
    position_error = float(np.linalg.norm(measured[0] - target[0]))
    orientation_error = _quaternion_distance(measured[1], target[1])
    return position_error, orientation_error


__all__ = ["PickPlaceController", "PickPlacePhase"]

```

## The failure to fix
Scene: the cube is picked at radius 0.80 m from the robot base, angle -60 degrees (pick position x = 0.400, y = -0.693 m). In three runs the controller lifted the cube, then timed out in the LIFT phase after 5 s with a tool position error of 0.0203 m against the 0.015 m convergence tolerance; the cube never reached the goal. Nearby scenes at radius 0.80-0.85 m fail the same way.

## What currently works
On development scenes the unchanged controller succeeded in all 36 runs on 12 hand-specified scenes, and in 44 of 45 runs on a grid of pick radii 0.35, 0.55 and 0.75 m at angles from -60 to 60 degrees. It failed all 30 runs at radii 0.80-0.85 m.

## Scoring
A run succeeds only if the cube is lifted above 7.58 cm and the run ends before the horizon, and over the final 30 frames the cube stays within 3.0 cm of the goal, released (gripper more than 8 cm away) and at rest (linear speed below 0.02 m/s, angular speed below 0.1 rad/s, orientation drift below 0.05 rad).

## Your memory: what earlier edits did
50 earlier edits to this controller were each tested on one fixed panel: 30 scenes near the failure (the unchanged controller solved 10) and 90 scenes across the workspace (it solved 73). For each edit: the parameters it changed (all others at their current values), target scenes newly solved / newly failed, workspace successes it broke (of 73), and workspace failures it fixed (of 17).

| # | Edit | Target scenes | Workspace successes broken | Workspace failures fixed |
|---|---|---|---|---|
| 1 | lift_height = 0.2 | +5 / -0 | 6 | 8 |
| 2 | position_tolerance = 0.025 | +18 / -1 | 4 | 7 |
| 3 | approach_height = 0.152 | +1 / -0 | 8 | 7 |
| 4 | grasp_position_tolerance = 0.012 | +0 / -0 | 0 | 0 |
| 5 | lift_height = 0.397, position_tolerance = 0.026 | +0 / -10 | 6 | 6 |
| 6 | position_tolerance = 0.033 | +19 / -0 | 3 | 9 |
| 7 | approach_height = 0.397, gripper_dwell = 0.21 | +0 / -10 | 7 | 5 |
| 8 | approach_height = 0.073, grasp_position_tolerance = 0.011 | +1 / -0 | 3 | 8 |
| 9 | position_tolerance = 0.012, gripper_dwell = 0.749 | +0 / -8 | 3 | 8 |
| 10 | lift_height = 0.395 | +0 / -10 | 10 | 7 |
| 11 | gripper_dwell = 0.134 | +0 / -0 | 3 | 5 |
| 12 | approach_height = 0.156 | +1 / -0 | 10 | 8 |
| 13 | stability_duration = 0.267 | +0 / -2 | 9 | 8 |
| 14 | lift_height = 0.361, position_tolerance = 0.009 | +0 / -10 | 10 | 5 |
| 15 | grasp_position_tolerance = 0.021 | +0 / -0 | 0 | 0 |
| 16 | approach_height = 0.178, position_tolerance = 0.026 | +20 / -0 | 16 | 10 |
| 17 | approach_height = 0.249, grasp_position_tolerance = 0.025 | +0 / -0 | 14 | 8 |
| 18 | grasp_position_tolerance = 0.026 | +0 / -0 | 0 | 0 |
| 19 | approach_height = 0.394 | +0 / -10 | 5 | 6 |
| 20 | gripper_dwell = 0.896 | +1 / -0 | 2 | 7 |
| 21 | approach_height = 0.062, grasp_position_tolerance = 0.018 | +1 / -0 | 5 | 7 |
| 22 | grasp_position_tolerance = 0.006, gripper_dwell = 0.44 | +0 / -0 | 15 | 6 |
| 23 | approach_height = 0.325 | +0 / -5 | 3 | 7 |
| 24 | stability_duration = 0.164 | +0 / -0 | 5 | 5 |
| 25 | approach_height = 0.244 | +0 / -1 | 12 | 7 |
| 26 | lift_height = 0.105, gripper_dwell = 0.202 | +5 / -0 | 4 | 9 |
| 27 | grasp_position_tolerance = 0.034 | +0 / -0 | 0 | 0 |
| 28 | grasp_position_tolerance = 0.021, gripper_dwell = 0.157 | +0 / -0 | 2 | 5 |
| 29 | grasp_position_tolerance = 0.022 | +0 / -0 | 0 | 0 |
| 30 | lift_height = 0.253 | +5 / -0 | 5 | 7 |
| 31 | lift_height = 0.343, position_tolerance = 0.018 | +0 / -10 | 2 | 4 |
| 32 | approach_height = 0.085 | +1 / -0 | 1 | 8 |
| 33 | position_tolerance = 0.013 | +0 / -6 | 6 | 5 |
| 34 | grasp_position_tolerance = 0.016, stability_duration = 0.454 | +0 / -5 | 2 | 8 |
| 35 | approach_height = 0.181, position_tolerance = 0.009 | +0 / -10 | 25 | 6 |
| 36 | grasp_position_tolerance = 0.011 | +0 / -0 | 0 | 0 |
| 37 | lift_height = 0.128, stability_duration = 0.432 | +0 / -3 | 1 | 9 |
| 38 | position_tolerance = 0.028 | +17 / -0 | 3 | 8 |
| 39 | approach_height = 0.168 | +1 / -0 | 14 | 7 |
| 40 | stability_duration = 0.068 | +0 / -0 | 3 | 8 |
| 41 | lift_height = 0.187 | +5 / -1 | 7 | 8 |
| 42 | lift_height = 0.303, position_tolerance = 0.026 | +18 / -0 | 2 | 4 |
| 43 | lift_height = 0.147, position_tolerance = 0.013 | +2 / -0 | 4 | 10 |
| 44 | gripper_dwell = 0.78 | +1 / -0 | 1 | 8 |
| 45 | stability_duration = 0.134 | +0 / -0 | 6 | 6 |
| 46 | position_tolerance = 0.03, grasp_position_tolerance = 0.019 | +20 / -0 | 2 | 8 |
| 47 | grasp_position_tolerance = 0.026, gripper_dwell = 0.215 | +0 / -0 | 0 | 0 |
| 48 | lift_height = 0.258 | +5 / -0 | 6 | 8 |
| 49 | gripper_dwell = 0.319 | +0 / -0 | 3 | 6 |
| 50 | lift_height = 0.24, gripper_dwell = 0.191 | +5 / -0 | 2 | 7 |

The workspace scenes these edits broke most often:
- radius 0.383 m, angle 2.1 degrees: broken by 19 of 50 edits
- radius 0.793 m, angle 17.8 degrees: broken by 15 of 50 edits
- radius 0.771 m, angle 39.4 degrees: broken by 12 of 50 edits
- radius 0.353 m, angle -0.3 degrees: broken by 12 of 50 edits
- radius 0.498 m, angle -26.1 degrees: broken by 11 of 50 edits
- radius 0.544 m, angle 33.9 degrees: broken by 10 of 50 edits
- radius 0.365 m, angle -13.9 degrees: broken by 9 of 50 edits
- radius 0.524 m, angle -38.7 degrees: broken by 9 of 50 edits
- radius 0.773 m, angle 21.6 degrees: broken by 9 of 50 edits
- radius 0.780 m, angle 30.7 degrees: broken by 8 of 50 edits

Of the 50 edits, 21 improved the target scenes; every one of these 21 also broke at least one workspace success. In 191 of the 260 broken workspace runs the controller still completed the motion but left the cube 3.0-4.7 cm from the goal, outside the 3 cm allowed.

## Your goal
Fix the failure above without breaking scenes the controller already solves. Your edit will be tested on scenes near the failing one and on scenes across the workspace.

## Answer format
Reply with only a JSON object, no other text:
{"overrides": {"<parameter>": <number>, ...}, "rationale": "<at most 3 sentences>", "expected_risk": "<at most 2 sentences>"}
Use 1 to 6 parameters from the table, each within its allowed range.
