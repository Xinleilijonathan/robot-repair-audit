"""Paired outcome audit. No simulator results are synthesized by this module."""
from __future__ import annotations

import argparse
import csv
import json
from collections import defaultdict
from pathlib import Path


def paired_metrics(parent: list[int], candidate: list[int]) -> dict:
    if not parent or len(parent) != len(candidate):
        raise ValueError("Need nonempty, equally sized paired observations")
    if any(x not in (0, 1) for x in parent + candidate):
        raise ValueError("Outcomes must be binary")
    n = len(parent)
    lost = sum(a == 1 and b == 0 for a, b in zip(parent, candidate))
    gained = sum(a == 0 and b == 1 for a, b in zip(parent, candidate))
    successes = sum(parent)
    return {
        "n": n,
        "parent_successes": successes,
        "candidate_successes": sum(candidate),
        "lost": lost,
        "gained": gained,
        "parent_success_rate": successes / n,
        "candidate_success_rate": sum(candidate) / n,
        "net_change": (gained - lost) / n,
        "unconditional_loss": lost / n,
        "conditional_loss": lost / successes if successes else None,
    }


def admit(old_parent, old_candidate, new_parent, new_candidate, max_lost_fraction=0.0):
    """Two rules consume exactly the same paired outcomes; neither certifies safety."""
    old = paired_metrics(old_parent, old_candidate)
    target = paired_metrics(new_parent, new_candidate)
    evaluable = old["parent_successes"] > 0
    aggregate = evaluable and target["net_change"] > 0 and old["net_change"] >= 0
    preservation = aggregate and old["conditional_loss"] <= max_lost_fraction
    return {
        "evaluable": evaluable,
        "aggregate": aggregate,
        "preservation": preservation,
        "logical_rollouts": 2 * (old["n"] + target["n"]),
        "old": old,
        "target": target,
    }


def audit_csv(path: Path) -> list[dict]:
    """Input has context_id,candidate_id,split,regime,scene_id,parent,candidate.

    Only split=audit is summarized. Validation and audit data are never pooled.
    Duplicated reset IDs in a context/candidate/regime are rejected.
    """
    groups = defaultdict(list)
    seen = set()
    with path.open(newline="", encoding="utf-8") as f:
        for row in csv.DictReader(f):
            if row["split"] != "audit":
                continue
            key = (row["context_id"], row["candidate_id"], row["regime"])
            identity = key + (row["scene_id"],)
            if identity in seen:
                raise ValueError(f"Duplicated paired observation: {identity}")
            seen.add(identity)
            groups[key].append((int(row["parent"]), int(row["candidate"])))
    if not groups:
        raise ValueError("No audit observations found; refusing an empty result")
    return [
        {"context_id": key[0], "candidate_id": key[1], "regime": key[2],
         **paired_metrics([a for a, _ in pairs], [b for _, b in pairs])}
        for key, pairs in sorted(groups.items())
    ]


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("csv", type=Path)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    result = audit_csv(args.csv)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(result, indent=2), encoding="utf-8")
    print(f"Audited {len(result)} context/candidate/regime groups")
