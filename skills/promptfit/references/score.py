#!/usr/bin/env python3
"""PromptFit deterministic scorer (stdlib only).

Usage:
    python3 score.py --mode json_field --pred outputs/ --gold expected/
    python3 score.py --mode exact      --pred outputs/ --gold expected/
    python3 score.py --mode token_f1   --pred outputs/ --gold expected/

Both --pred and --gold must be FLAT directories whose files are matched by stem — the stem IS the
example id (e.g. outputs/ex04.txt <-> expected/ex04.json). Subdirectories are ignored; if your data
is one-subdir-per-example, flatten it into id-keyed files first (see references/evaluators.md).

Prints a JSON summary to stdout:
{"mode":..., "mean": <float 0..1>, "n": <int>, "per_example": {stem: score, ...}, "warnings": [...]}
"warnings" is non-empty when the match looks suspicious (ignored subdirs, missing preds, n=0); those
same warnings are also printed to stderr. Read them before trusting "mean".
Exit code 0 always (scoring is not a failure); an unreadable or unparseable item yields score 0.
"""
import argparse
import json
import sys
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
    gold_dir, pred_dir = Path(args.gold), Path(args.pred)
    gold_by_stem = {p.stem: p for p in gold_dir.glob("*") if p.is_file()}
    pred_by_stem = {p.stem: p for p in pred_dir.glob("*") if p.is_file()}

    # Guard against silently scoring the wrong thing (e.g. a subdir-per-example dataset
    # pointed at directly, which matches 0 real examples yet would otherwise look like a clean run).
    warnings = []
    ignored_subdirs = [p.name for p in gold_dir.glob("*") if p.is_dir()]
    if ignored_subdirs:
        warnings.append(
            f"{len(ignored_subdirs)} subdirectory(ies) in --gold were ignored; score.py compares "
            "FLAT id-keyed files (e.g. gold/ex04.json). Flatten the dataset before scoring."
        )
    missing = sorted(s for s in gold_by_stem if s not in pred_by_stem)
    if missing:
        warnings.append(f"{len(missing)} gold example(s) had no matching --pred file (scored 0): {missing[:10]}")
    if not gold_by_stem:
        warnings.append("no gold files matched (n=0); check the --gold path and layout.")

    per = {}
    for stem, gpath in sorted(gold_by_stem.items()):
        ppath = pred_by_stem.get(stem)
        if ppath is None:
            per[stem] = 0.0
            continue
        try:
            per[stem] = round(scorer(_load(ppath), _load(gpath)), 4)
        except (OSError, UnicodeDecodeError):
            # honor the module contract: an unreadable item scores 0, never crashes the run
            per[stem] = 0.0

    mean = round(sum(per.values()) / len(per), 4) if per else 0.0
    for w in warnings:
        print(f"WARNING: {w}", file=sys.stderr)
    print(json.dumps({"mode": args.mode, "mean": mean, "n": len(per), "per_example": per, "warnings": warnings}))
    return 0


if __name__ == "__main__":
    sys.exit(main())
