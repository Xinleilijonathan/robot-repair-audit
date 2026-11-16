# Workspace-boundary development amendment

> **Correction, added Nov 15 ~15:00, original text unchanged below.** The radial panel did *not* have zero failures. `r75_a+60` failed on repeat 1 (0.0308 m placement error; 44/45 successes per `results/radial_parent/summary.json`). The radial rule selected a target only for a scene failing at least 2 of 3 repeats, so no radial target qualified, and this boundary extension still followed the documented procedure.

November 15, after completion of the 45-rollout radial panel, which had no failures. This is a second adaptive development search, not a prespecified benchmark population or a final audit.

Test pick radii 0.80 and 0.85 m at all five existing angles (-60, -30, 0, 30, 60 degrees), three resets per scene. Keep pick height, place, parent controller, evaluator, and horizon unchanged. Record all 30 outcomes. These positions probe the reach boundary; unreachable cases may occur and must not be called proven repair opportunities. Do not extend the radius again in this pilot session.

Select the first scene in manifest order failing at least two of three repetitions. Generate exactly two bounded proposals from its trace and the installed controller source. Save both before candidate execution. If no repeatable failure is found, stop failure discovery and report the simple-task ceiling.

For candidate comparison, use all 25 radial+boundary scenes with three resets each (75 per candidate). Re-run the unchanged parent on the same full ordered panel after both candidates (75 more). This replaces the earlier 15-scene candidate panel; no interior successes or boundary failures are excluded. Compare candidate results to the complete repeated-parent panel as the primary development diagnostic, and compare original discovery outcomes to that parent panel to expose reset/order variability. The selected target is the same throughout. The added panel costs are development costs, not matched gate-validation evidence.

If both proposals fail to repair the target, do not generate more proposals for that target in this pilot. Record the failed repair attempt and make an explicit paper-scope decision. Do not claim that boundary failures must be repairable or that parameter editing establishes general robot learning.
