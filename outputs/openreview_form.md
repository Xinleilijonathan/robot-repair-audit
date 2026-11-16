# OpenReview submission form: draft entries

Venue: AAAI 2027 Workshop on Trustworthy Evolution of AI Agents (Trust4RSI-Agent). Form: https://openreview.net/group?id=AAAI.org/2027/Workshop/Trust4RSI-Agent. The form closes Nov 21, 13:00 UTC, which is Nov 20 AoE.

These fields come from the live submission form, read Nov 16. **Nothing has been submitted.**

## Title

Repair Without Regression? A Budget-Matched Audit of an Agent-Edited Robot Skill

## Authors (required)

- Every author needs an OpenReview profile **before** submitting.
- Create or check yours now, using your institutional email; new profiles can take time to be approved.
- Enter your affiliation exactly as you want it to appear.

## Keywords (required, comma-separated)

regression testing, update admission, self-improving agents, robot skills, controller repair, paired evaluation, Isaac Sim, trustworthy agent evolution

## TL;DR (optional, at most 250 characters)

In a fully replayable simulated robot skill, every controller edit that improved the target also broke previously solved scenes, and whether aggregate success exposed this depended on which old scenes were sampled.

## Abstract (required)

Paste the abstract that matches the PDF you upload.

### If you upload `paper/main.pdf` (full version)

When a coding agent edits a persistent robot controller to fix a failure, aggregate success can hide losses on scenes the controller used to solve. We test this in a small, fully controlled case: the scripted Franka pick-and-place controller in Isaac Sim, a measured-state evaluator that rejects four negative controls, and a workspace-boundary failure found by documented search. The unchanged controller replays exactly, so every paired transition is caused by an edit. On the development panel, two frozen single-parameter repairs each fixed the target and lost 4 and 1 of 44 earlier successes, but gained more elsewhere, so aggregate and zero-loss admission disagreed. On a frozen audit of 160 fresh scenes this compensation did not replicate. Both repairs improved the target neighborhood (from 15/40 to 26/40 and 38/40) but lost 8 and 5 of 106 old successes against 4 gains each, and budget-matched aggregate and zero-loss gates, committed before the audit, both rejected both. A post-hoc extension tested 24 seeded random edits alongside the two repairs on a fresh draw. All ten candidates that improved the target lost old successes, and the two repairs' old net change turned positive while their conditional loss rates replicated. Every loss of a target-improving candidate was a centimeter-scale placement regression far from the repaired boundary. In this case the composition of the old-scene panel mattered more than the choice between aggregate and zero-loss admission.

### If you upload `paper/main_short.pdf` (4 pages including references)

When a coding agent edits a persistent robot controller to fix a failure, aggregate success can hide losses on scenes the controller used to solve. We test this in a fully controlled case: the scripted Franka pick-and-place controller in Isaac Sim, a measured-state evaluator, and a workspace-boundary failure found by documented search. The unchanged controller replays exactly, so every paired transition is caused by an edit. On the development panel, two frozen single-parameter repairs fixed the target and lost 4 and 1 of 44 earlier successes but gained more elsewhere, so aggregate and zero-loss admission disagreed. On a frozen audit of 160 fresh scenes this compensation did not replicate. Both repairs improved the target neighborhood (from 15/40 to 26/40 and 38/40) but lost 8 and 5 of 106 old successes against 4 gains each, and budget-matched aggregate and zero-loss gates both rejected both. In a post-hoc extension with 24 seeded random edits, all ten target-improving candidates lost old successes. On that fresh draw the two repairs' old net change turned positive, while their conditional loss rates replicated. The composition of the old-scene panel mattered more than the choice of admission rule.

## PDF (required, at most 50 MB)

The form has no field for supplementary material, so the paper says the artifact "will be released after the review period."

- **Organizers confirm references are excluded:** upload `paper/main.pdf`.
- **No confirmation by Nov 18:** upload `paper/main_short.pdf`.

## Required confirmations (read before ticking)

- **Email sharing:** "We authorize the sharing of all author emails with Program Chairs."
- **Data release:** "We authorize the release of our submission and author names to the public in the event of acceptance."
