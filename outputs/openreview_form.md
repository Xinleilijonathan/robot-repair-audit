# OpenReview submission form: draft entries

Venue: AAAI 2027 Workshop on Trustworthy Evolution of AI Agents (Trust4RSI-Agent). Form: https://openreview.net/group?id=AAAI.org/2027/Workshop/Trust4RSI-Agent. The form closes Nov 21, 13:00 UTC, which is Nov 20 AoE.

These fields come from the live submission form, read Nov 16. **Nothing has been submitted.**

**Version (user decision, Nov 17):** submit the Extension 2 drafts, `paper/main_ext2.pdf` or `paper/main_ext2_short.pdf`. The entries below match them. `main.pdf` and `main_short.pdf` are the earlier version without the pre-registered test and are no longer the submission.

## Title

Repair Without Regression? A Budget-Matched Audit of an Agent-Edited Robot Skill

## Authors (required)

- Every author needs an OpenReview profile **before** submitting.
- Create or check yours now, using your institutional email; new profiles can take time to be approved.
- Enter your affiliation exactly as you want it to appear.

## Keywords (required, comma-separated)

regression testing, test prioritization, update admission, self-improving agents, robot skills, controller repair, paired evaluation, pre-registration, Isaac Sim, trustworthy agent evolution

## TL;DR (optional, at most 250 characters)

In a replayable simulated robot skill, all 21 audited edits that improved the target broke old scenes. In a pre-registered test, 8 scenes chosen from what past edits broke caught a regression in 14/20 new edits, vs 36% expected for 8 random ones.

(246 characters.)

## Abstract (required)

Paste the abstract that matches the PDF you upload. It is the paper's abstract converted to plain text.

### If you upload `paper/main_ext2.pdf` (4-page body, references on page 5)

When a coding agent edits a persistent robot controller to fix a failure, aggregate success can hide losses on scenes the controller used to solve. We test this in a fully controlled case: the scripted Franka pick-and-place controller in Isaac Sim, a measured-state evaluator, and a workspace-boundary failure found by documented search. The unchanged controller replays exactly, so every paired transition is caused by an edit. On the development panel, two frozen repairs fixed the target and lost 4 and 1 of 44 earlier successes but gained more elsewhere, so aggregate and zero-loss admission disagreed. On a frozen audit of 160 fresh scenes this compensation did not replicate: both repairs improved the target neighborhood (from 15/40 to 26/40 and 38/40) but lost 8 and 5 of 106 old successes, and budget-matched gates committed before the audit rejected both. In two further populations, all 21 target-improving candidates lost old successes, and different edits broke the same fragile scenes. In a pre-registered test on the 24 new edits, an 8-scene suite built from earlier edits' losses detected a loss in 14 of the 20 edits that had one, against 36% expected for 8 random old scenes (difference +0.34, 95% CI 0.16–0.51). In this case the composition of the old-scene panel mattered more than the choice of admission rule, and the record of what past updates broke was a cheap regression suite for the next one.

### If you upload `paper/main_ext2_short.pdf` (4 pages including references)

When a coding agent edits a persistent robot controller to fix a failure, aggregate success can hide losses on scenes the controller used to solve. We test this in a fully controlled case: the scripted Franka pick-and-place controller in Isaac Sim, whose unchanged version replays exactly, so every paired transition is caused by an edit. On the development panel, two frozen repairs of a boundary failure lost 4 and 1 of 44 earlier successes but gained more elsewhere, so aggregate and zero-loss admission disagreed. On a frozen audit of 160 fresh scenes this compensation did not replicate: both repairs improved the target neighborhood (from 15/40 to 26/40 and 38/40) but lost 8 and 5 of 106 old successes, and gates committed before the audit rejected both. In two further populations, all 21 target-improving candidates lost old successes, and different edits broke the same fragile scenes. In a pre-registered test on 24 new edits, an 8-scene suite built from earlier edits' losses detected a loss in 14 of the 20 edits that had one, against 36% expected for 8 random old scenes (difference +0.34, 95% CI 0.16–0.51). Panel composition mattered more than the admission rule, and the record of what past updates broke was a cheap regression suite for the next one.

## PDF (required, at most 50 MB)

The form has no field for supplementary material, so the paper says the anonymized artifact will be "released after review."

- **Organizers confirm references are excluded:** upload `paper/main_ext2.pdf`.
- **No confirmation by Nov 18:** upload `paper/main_ext2_short.pdf`.

## Required confirmations (read before ticking)

- **Email sharing:** "We authorize the sharing of all author emails with Program Chairs."
- **Data release:** "We authorize the release of our submission and author names to the public in the event of acceptance."
