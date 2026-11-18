# OpenReview submission form: draft entries

Venue: AAAI 2027 Workshop on Trustworthy Evolution of AI Agents (Trust4RSI-Agent). Form: https://openreview.net/group?id=AAAI.org/2027/Workshop/Trust4RSI-Agent. The form closes Nov 21, 13:00 UTC, which is Nov 20 AoE.

These fields come from the live submission form, read Nov 16. **Nothing has been submitted.**

**Version (user decision, Nov 17; Extension 3 added Nov 18 at the user's request):** submit the Extension 2 drafts, `paper/main_ext2.pdf` or `paper/main_ext2_short.pdf`, which now also include the agent-proposed-repair test. The entries below match them. `main.pdf` and `main_short.pdf` are the earlier version without the pre-registered test and are no longer the submission.

## Title

Repair Without Regression? A Budget-Matched Audit of an Agent-Edited Robot Skill

## Authors (required)

- Every author needs an OpenReview profile **before** submitting.
- Create or check yours now, using your institutional email; new profiles can take time to be approved.
- Enter your affiliation exactly as you want it to appear.

## Keywords (required, comma-separated)

regression testing, test prioritization, update admission, self-improving agents, robot skills, controller repair, paired evaluation, pre-registration, Isaac Sim, trustworthy agent evolution

## TL;DR (optional, at most 250 characters)

In a replayable simulated robot skill, all 24 distinct edits that improved the target broke old scenes, including 7 proposed by AI models. Eight scenes chosen from what past edits broke caught a regression in 14/20 new random edits and 6/7 AI ones.

(248 characters.)

## Abstract (required)

Paste the abstract that matches the PDF you upload. It is the paper's abstract converted to plain text. Since Nov 18 both PDFs have the same abstract.

### If you upload `paper/main_ext2.pdf` (4-page body, references on page 5)

When a coding agent edits a persistent robot controller to fix a failure, aggregate success can hide losses on scenes the controller used to solve. We study this in a controlled case: the scripted Franka pick-and-place controller in Isaac Sim, which replays exactly for a fixed scene order, so every paired transition is caused by an edit. Edits set bounded controller parameters rather than code. Across two frozen repairs, 48 seeded random edits and 7 distinct edits proposed by four AI models, every edit that improved the target lost old successes, and different edits broke the same fragile scenes. Two pre-registered tests show that an 8-scene suite built from earlier edits' losses catches new regressions about twice as often as random old scenes (14 of 20 random and 6 of 7 agent edits, against 36% and 39% expected), although 4 agent edits repeated earlier ones. As a zero-loss gate, the suite also rejects almost every useful edit, because no improvement was loss-free. Whether aggregate and zero-loss admission disagree depended more on the old-scene panel than on the rule: compensating gains seen on a development panel built around the failure vanished on a frozen audit of fresh scenes.

### If you upload `paper/main_ext2_short.pdf` (4 pages including references)

When a coding agent edits a persistent robot controller to fix a failure, aggregate success can hide losses on scenes the controller used to solve. We study this in a controlled case: the scripted Franka pick-and-place controller in Isaac Sim, which replays exactly for a fixed scene order, so every paired transition is caused by an edit. Edits set bounded controller parameters rather than code. Across two frozen repairs, 48 seeded random edits and 7 distinct edits proposed by four AI models, every edit that improved the target lost old successes, and different edits broke the same fragile scenes. Two pre-registered tests show that an 8-scene suite built from earlier edits' losses catches new regressions about twice as often as random old scenes (14 of 20 random and 6 of 7 agent edits, against 36% and 39% expected), although 4 agent edits repeated earlier ones. As a zero-loss gate, the suite also rejects almost every useful edit, because no improvement was loss-free. Whether aggregate and zero-loss admission disagree depended more on the old-scene panel than on the rule: compensating gains seen on a development panel built around the failure vanished on a frozen audit of fresh scenes.

## PDF (required, at most 50 MB)

The form has no field for supplementary material, so the paper says the anonymized artifact will be "released after review."

- **Organizers confirm references are excluded:** upload `paper/main_ext2.pdf`.
- **No confirmation by Nov 18:** upload `paper/main_ext2_short.pdf`.

## Required confirmations (read before ticking)

- **Email sharing:** "We authorize the sharing of all author emails with Program Chairs."
- **Data release:** "We authorize the release of our submission and author names to the public in the event of acceptance."
