# Additional development variation rule

Specified November 15 during the original twelve-scene evaluation, before any radial-grid outcome. Execute if the original twelve scenes provide no repeatably failed target. This is exploratory failure discovery, not held-out testing.

Use all combinations of pick radius {0.35, 0.55, 0.75} m and planar angle {-60, -30, 0, 30, 60} degrees around the robot origin; pick height 0.0258 m, place [0, 0.5, 0.0258] m. Order by ascending radius, then angle. Run each scene three times with the unchanged parent and v2 scorer. Fifteen scenes, 45 rollouts. The outer radius intentionally probes the workspace boundary; reachability is not assumed. Keep unreachable cases in development accounting and do not represent them as proven repairable failures.

If a scene fails at least two of three repeats, select the first such scene in manifest order for the first two-proposal pilot. If no scene meets this rule, record that outcome before considering further task changes. If this grid is used, replace the twelve-scene candidate/repeated-parent panel in pilot_protocol.md with this entire fifteen-scene grid. Do not remove inconvenient cases or alter tolerances after observing outcomes. Target is the selected scene; the other fourteen constitute the exploratory old panel. This amendment is specified before grid outcomes.

The lower approach/lift heights already permitted by the controller interface may help boundary approaches; other causes may not be repairable by those parameters. Proposals will be recorded from actual failure traces. This rationale is not a prediction of success.
