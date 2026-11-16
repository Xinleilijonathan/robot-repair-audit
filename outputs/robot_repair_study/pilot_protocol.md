# Exploratory repair pilot protocol

Recorded November 15, 2026, during the remaining-six-scene run. The first five rollouts (all successful) had been inspected; no failure or candidate outcome had been inspected. This is a development protocol, not a preregistration.

## Scope and provenance

This pilot uses the unchanged NVIDIA Franka parent, the version 2 measured-state evaluator, and the twelve already specified development scenes. It does not use a final audit split. No evaluator threshold, initial parent parameter, or scene is changed to force gate disagreement.

Start by evaluating the remaining six scenes three times each. If none fail, specify a physically plausible development variation rule before running that additional set. Retain every outcome. This adaptive development search is not a prevalence sample of robot failures.

For the first repeatable failure in manifest order, propose two bounded parameter configurations, at most six parameters per configuration. The assistant may inspect the installed controller/task source and development traces. Save the exact configurations and their rationale before running either candidate. Both proposals must be evaluated, including unsuccessful proposals. Do not replace a proposal after seeing its outcome. Additional contexts, up to five total, require separately logged proposals and remain exploratory.

Proposal generation is interactive Codex assistance with the full prior conversation and development outputs available. A standalone frozen model API is not configured. A saved task instruction is a record of the local proposal request, not a claim to reconstruct the full model context or stochastic sampling parameters. Findings cannot establish an independent model benchmark or a special benefit from failure feedback.

## Evaluation and accounting

Use the same twelve development scenes and three repeats for each candidate. Run a fresh parent panel after candidates to check repeatability and order sensitivity. Preserve every raw rollout, exact runner snapshot, metadata, and process log. A failed launch is an infrastructure outcome, not a robot failure; a completed unsuccessful rollout remains a behavioral failure. Mark aborted/partial batches explicitly and never silently overwrite them.

Report valid proposals/all proposals; target repair outcomes; all paired transition cells; old-success losses and old-failure gains; and outcomes under both hypothetical gates. Pair scene/repeat labels cautiously: resets show small state variation, so transitions can reflect simulator variation. Compare with the repeated parent before attributing differences to a controller edit. Repeats are not independent repair candidates.

The intended equal-budget gates are unchanged, but this pilot's full-panel summaries are diagnostics, not the frozen four-target/eight-old validation experiment. A target is the first repeatably failed scene; all other development scenes constitute the exploratory old panel. Gate disagreement is informative only if old losses are compensated by old gains and target performance improves.

## Decision

Proceed to a frozen empirical protocol only after observed repairs, informative comparison opportunities, and sufficient reset reliability. Otherwise write a transparently scoped pilot/position paper or defer. No hypothetical results, manufactured failures, or post hoc held-out labels are permitted.
