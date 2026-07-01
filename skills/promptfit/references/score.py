#!/usr/bin/env python3
"""PromptFit deterministic scorer (stdlib only).

Usage:
    python3 score.py --mode json_field --pred outputs/ --gold expected/
    python3 score.py --mode exact      --pred outputs/ --gold expected/
    python3 score.py --mode token_f1   --pred outputs/ --gold expected/

Files are matched by stem (e.g. outputs/ex04.txt <-> expected/ex04.json). Prints a JSON summary:
{"mode":..., "mean": <float 0..1>, "n": <int>, "per_example": {stem: score, ...}}
Exit code 0 always (scoring is not a failure); parse issues yield score 0 for that item.
"""
import argparse
import json
import sys
from difflib import SequenceMatcher
from pathlib import Path


def _load(path: Path) -> str:
    return path.read_text(encoding="utf-8").strip()


def exact(pred: str, gold: str) -> float:
    return 1.0 if pred.strip() == gold.strip() else 0.0


def _try_json(s: str):
    try:
        return json.loads(s)
    except (json.JSONDecodeError, ValueError):
        return None


def json_field(pred: str, gold: str) -> float:
    """Fraction of gold top-level keys whose value matches pred's (order-insensitive)."""
    g = _try_json(gold)
    p = _try_json(pred)
    if not isinstance(g, dict):
        return exact(pred, gold)  # gold isn't JSON: fall back to exact
    if not isinstance(p, dict):
        return 0.0
    if not g:
        return 1.0 if p == g else 0.0
    hits = sum(1 for k, v in g.items() if k in p and p[k] == v)
    return hits / len(g)


def token_f1(pred: str, gold: str) -> float:
    pt = pred.split()
    gt = gold.split()
    if not pt and not gt:
        return 1.0
    if not pt or not gt:
        return 0.0
    # multiset overlap
    from collections import Counter
    cp, cg = Counter(pt), Counter(gt)
    overlap = sum((cp & cg).values())
    if overlap == 0:
        return 0.0
    precision = overlap / len(pt)
    recall = overlap / len(gt)
    return 2 * precision * recall / (precision + recall)


SCORERS = {"exact": exact, "json_field": json_field, "token_f1": token_f1}


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--mode", required=True, choices=sorted(SCORERS))
    ap.add_argument("--pred", required=True, help="dir of predicted output files")
    ap.add_argument("--gold", required=True, help="dir of expected output files")
    args = ap.parse_args()

    scorer = SCORERS[args.mode]
    gold_by_stem = {p.stem: p for p in Path(args.gold).glob("*") if p.is_file()}
    pred_by_stem = {p.stem: p for p in Path(args.pred).glob("*") if p.is_file()}

    per = {}
    for stem, gpath in sorted(gold_by_stem.items()):
        ppath = pred_by_stem.get(stem)
        if ppath is None:
            per[stem] = 0.0
            continue
        per[stem] = round(scorer(_load(ppath), _load(gpath)), 4)

    mean = round(sum(per.values()) / len(per), 4) if per else 0.0
    print(json.dumps({"mode": args.mode, "mean": mean, "n": len(per), "per_example": per}))
    return 0


if __name__ == "__main__":
    sys.exit(main())
