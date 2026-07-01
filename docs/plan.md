# PromptFit Skill Implementation Plan

> **STATUS — Implemented & merged to `main` (2026-07-01).** All 11 tasks were built; a review-driven
> hardening pass then changed several files. The verbatim file blocks below reflect the **original
> plan**, not the final shipped state — for current content read the files under `skills/promptfit/`
> and `scripts/`, and `docs/design.md` (reconciled). Post-plan changes: added
> `.claude-plugin/marketplace.json`; `score.py` gained a `warnings` array + graceful per-item
> degradation and dropped the unused `SequenceMatcher` import; the deterministic path now uses a flat,
> id-keyed `gold/` + `outputs/` layout cleared each iteration; `evaluators.md` / `loop-spec.md` /
> `SKILL.md` / `validate.sh` were expanded to match.

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build `promptfit`, a Claude Code plugin whose skill trains a portable, provider-agnostic system prompt from labeled input→output examples via an ML-style loop (train/val/test, eval-scored accept/reject, early stopping), running Claude-native with no install.

**Architecture:** A plugin repo containing one skill (`skills/promptfit/SKILL.md`) that orchestrates a guided workflow, four reference docs it reads on demand, one stdlib `score.py` template it copies into each project for deterministic scoring, and a bundled example dataset used as a smoke test. All loop logic lives in skill instructions executed by Claude; the only executable code is `score.py`.

**Tech Stack:** Markdown (SKILL.md + references), JSON (plugin manifest, example labels), Python 3 stdlib (`score.py` — `json`, `difflib`, `argparse`, `pathlib`), git.

**Reference:** Approved design spec at `docs/design.md`; prior-art at `docs/research-notes.md`. Read `docs/design.md` before starting — it is the source of truth for every behavior below.

---

## File structure (locked)

```
promptfit/
├── .claude-plugin/plugin.json          # Task 1 — plugin manifest
├── .claude-plugin/marketplace.json     # (post-plan) marketplace catalog for /plugin marketplace add
├── README.md                           # Task 2 — what it is + install
├── examples/
│   ├── README.md                       # Task 3 — dataset description + schema
│   └── ex01..ex12/{input.txt,expected_output.json}   # Task 3 — 12 labeled bundles
├── skills/promptfit/
│   ├── references/
│   │   ├── score.py                    # Task 4 — deterministic evaluator template
│   │   ├── optimizer-prompt.md         # Task 6 — the PE-agent prompt
│   │   ├── evaluators.md               # Task 7 — evaluator selection + recipes
│   │   ├── loop-spec.md                # Task 8 — exact loop, split, budget
│   │   └── lineage.md                  # Task 9 — prior art + differentiation
│   └── SKILL.md                        # Task 5 & 10 — entry point / guided workflow
└── scripts/validate.sh                 # Task 11 — repo self-check
```

Task order builds leaves before the root: manifest → README → dataset → score.py (+test) → SKILL skeleton → references → SKILL full workflow → validation.

---

### Task 1: Plugin manifest

**Files:**
- Create: `.claude-plugin/plugin.json`

- [ ] **Step 1: Write the manifest**

```json
{
  "name": "promptfit",
  "version": "0.1.0",
  "description": "Fit a portable system prompt to your labeled input→output examples via an iterative ML loop — train/val/test split, eval-scored accept/reject, early stopping.",
  "author": { "name": "Toni" },
  "homepage": "https://github.com/NiccoloTogni/promptfit",
  "keywords": ["prompt-optimization", "prompt-engineering", "evals", "distillation", "skill"]
}
```

- [ ] **Step 2: Verify it is valid JSON**

Run: `python3 -c "import json,sys; json.load(open('.claude-plugin/plugin.json')); print('OK')"`
Expected: `OK`

- [ ] **Step 3: Commit**

```bash
git add .claude-plugin/plugin.json
git commit -m "feat: add plugin manifest"
```

---

### Task 2: README

**Files:**
- Create: `README.md`

- [ ] **Step 1: Write `README.md`**

Content (verbatim):

```markdown
# PromptFit

Fit a **portable system prompt** to your labeled `input → expected_output` examples with an
ML-style loop: seeded train/val/test split, an optimizer step that rewrites the prompt from a
batch + accumulated learnings, eval-scored **accept/reject**, and **early stopping**. The trained
prompt is the deliverable — a plain text file you can paste into any provider. "The prompt is the model."

Runs **Claude-native**: no Python package and no API key for the core path. For very large jobs,
binary inputs, RAG-matched eval, or DB storage, graduate to the [prompt-forge](https://github.com/NiccoloTogni/prompt-forge)
library or DSPy/GEPA (see `skills/promptfit/references/lineage.md`).

## What makes it different

PromptFit is **not a new algorithm** — it's the well-known LLM-as-optimizer / textual-gradient-descent
family (ProTeGi, TextGrad, OPRO, GEPA; DSPy/MIPROv2 is the Bayesian cousin). Existing prompt-optimizer
skills tune *an agent's own `skill.md`*. PromptFit instead trains a **standalone, provider-agnostic
prompt** from *your* labeled data, with classical-ML rigor (train/val/test, accept/reject, versioning)
and **flexible ingestion** (bring your data however it is). See `references/lineage.md`.

## Install

- **Plugin:** add this repo as a plugin marketplace in Claude Code, then `/plugin install promptfit`.
- **Copy-in:** copy `skills/promptfit/` into `~/.claude/skills/`.

Then run `/promptfit` and point it at a folder of labeled examples.

## Requirements

Core path needs only Claude Code. Deterministic scoring uses the ambient Python 3 (stdlib only);
if Python is unavailable it falls back to careful inline scoring (flagged as less reproducible).
```

- [ ] **Step 2: Verify links/paths referenced exist later** — no action now; confirmed by Task 11.

- [ ] **Step 3: Commit**

```bash
git add README.md
git commit -m "docs: add README"
```

---

### Task 3: Bundled example dataset (smoke test)

**Files:**
- Create: `examples/README.md`
- Create: `examples/ex01/input.txt` … `examples/ex12/input.txt`
- Create: `examples/ex01/expected_output.json` … `examples/ex12/expected_output.json`

**Task:** support-email field extraction. Each `input.txt` is a short customer email; each
`expected_output.json` has exactly these keys: `intent` (one of `refund`, `cancel`, `technical`,
`billing`, `praise`, `other`), `product` (string or null), `urgency` (`low`|`medium`|`high`),
`wants_refund` (boolean). This exercises JSON-field eval, enums, nulls, and booleans.

- [ ] **Step 1: Write `examples/README.md`**

```markdown
# Example dataset — support-email extraction

12 labeled examples. Layout: one folder per example, `input.txt` (a short support email) +
`expected_output.json`. Schema (all keys required):

- `intent`: one of `refund`, `cancel`, `technical`, `billing`, `praise`, `other`
- `product`: the product mentioned, or `null`
- `urgency`: `low`, `medium`, or `high`
- `wants_refund`: boolean

Used as PromptFit's smoke test: `/promptfit` should ingest this folder, split, train, and produce
a prompt that maps an email to this JSON. Deterministic evaluator = `json_field`.
```

- [ ] **Step 2: Create the 12 bundles**

For each row, create `examples/exNN/input.txt` with the Email text and `examples/exNN/expected_output.json` with the JSON (compact, keys in this order: intent, product, urgency, wants_refund).

| NN | Email (input.txt) | expected_output.json |
|----|-------------------|----------------------|
| 01 | `My Nimbus router keeps dropping wifi every hour. Please help, I work from home.` | `{"intent":"technical","product":"Nimbus router","urgency":"high","wants_refund":false}` |
| 02 | `I was charged twice for my subscription this month. Can you sort this out?` | `{"intent":"billing","product":null,"urgency":"medium","wants_refund":false}` |
| 03 | `Please cancel my account, I no longer need the service.` | `{"intent":"cancel","product":null,"urgency":"low","wants_refund":false}` |
| 04 | `The Aero headphones broke after two days. I want my money back.` | `{"intent":"refund","product":"Aero headphones","urgency":"high","wants_refund":true}` |
| 05 | `Just wanted to say your support team was fantastic yesterday. Thanks!` | `{"intent":"praise","product":null,"urgency":"low","wants_refund":false}` |
| 06 | `The Pixel Pro app crashes every time I open the camera tab.` | `{"intent":"technical","product":"Pixel Pro app","urgency":"medium","wants_refund":false}` |
| 07 | `I'd like a refund for the Orbit smartwatch — it never matched the description.` | `{"intent":"refund","product":"Orbit smartwatch","urgency":"medium","wants_refund":true}` |
| 08 | `Why is my invoice in euros when I pay in dollars? Confusing.` | `{"intent":"billing","product":null,"urgency":"low","wants_refund":false}` |
| 09 | `Cancel the Vera Plus plan before the next renewal please, it renews tomorrow.` | `{"intent":"cancel","product":"Vera Plus","urgency":"high","wants_refund":false}` |
| 10 | `Hi, do you ship to Canada? Just a quick question.` | `{"intent":"other","product":null,"urgency":"low","wants_refund":false}` |
| 11 | `The Lumen lamp arrived shattered. Refund me and I don't want a replacement.` | `{"intent":"refund","product":"Lumen lamp","urgency":"high","wants_refund":true}` |
| 12 | `Login has been broken for three days and nobody replied to my ticket.` | `{"intent":"technical","product":null,"urgency":"high","wants_refund":false}` |

- [ ] **Step 3: Verify all labels parse and count is 12**

Run:
```bash
python3 -c "
import json,glob
fs=sorted(glob.glob('examples/ex*/expected_output.json'))
assert len(fs)==12, len(fs)
keys={'intent','product','urgency','wants_refund'}
for f in fs:
    d=json.load(open(f)); assert set(d)==keys, (f,set(d))
print('OK', len(fs))
"
```
Expected: `OK 12`

- [ ] **Step 4: Commit**

```bash
git add examples/
git commit -m "test: add support-email example dataset (smoke test)"
```

---

### Task 4: `score.py` deterministic evaluator template

**Files:**
- Create: `skills/promptfit/references/score.py`

This is the reusable scorer the skill copies into each project. It reads a directory of predicted
outputs and a directory of expected outputs (matched by filename stem) and prints a mean score in
[0,1] plus per-example detail. Supports `exact`, `json_field`, `token_f1`.

- [ ] **Step 1: Write `score.py`**

> ⚠️ **Superseded post-implementation** — the shipped `skills/promptfit/references/score.py` adds a
> `warnings` array + graceful per-item degradation and drops the `SequenceMatcher` import. Treat the
> shipped file as source of truth; the block below is the original plan.

```python
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
```

- [ ] **Step 2: Create a throwaway fixture and verify a perfect score**

Run:
```bash
tmp=$(mktemp -d)
mkdir -p "$tmp/pred" "$tmp/gold"
printf '{"intent":"refund","product":"Aero headphones","urgency":"high","wants_refund":true}' > "$tmp/gold/ex04.json"
printf '{"wants_refund":true,"intent":"refund","product":"Aero headphones","urgency":"high"}' > "$tmp/pred/ex04.json"
python3 skills/promptfit/references/score.py --mode json_field --pred "$tmp/pred" --gold "$tmp/gold"
```
Expected: `{"mode": "json_field", "mean": 1.0, "n": 1, "per_example": {"ex04": 1.0}}`

- [ ] **Step 3: Verify a partial score (one wrong field of four)**

Run:
```bash
printf '{"intent":"cancel","product":"Aero headphones","urgency":"high","wants_refund":true}' > "$tmp/pred/ex04.json"
python3 skills/promptfit/references/score.py --mode json_field --pred "$tmp/pred" --gold "$tmp/gold"
rm -rf "$tmp"
```
Expected: `{"mode": "json_field", "mean": 0.75, "n": 1, "per_example": {"ex04": 0.75}}`

- [ ] **Step 4: Commit**

```bash
git add skills/promptfit/references/score.py
git commit -m "feat: add deterministic score.py evaluator template"
```

---

### Task 5: SKILL.md skeleton (frontmatter + trigger)

**Files:**
- Create: `skills/promptfit/SKILL.md`

Create the file with valid frontmatter and a one-paragraph body. The full workflow body is added in
Task 10 (after the references it links to exist).

- [ ] **Step 1: Write the skeleton**

```markdown
---
name: promptfit
description: Fit a portable system prompt to labeled input→output examples via an iterative ML loop — seeded train/val/test split, an optimizer step that rewrites the prompt from a batch plus accumulated learnings, eval-scored accept/reject, and early stopping. Use when someone wants to "learn", "optimize", "distill", or "train" a reusable system prompt from labeled examples (extraction, classification, structured-output tasks) rather than tune an agent's own skill.md. Not for editing this agent's behavior.
---

# PromptFit

Train a portable, provider-agnostic **system prompt** from labeled `input → expected_output` examples.
The trained prompt is the deliverable. This runs Claude-native — Claude is the optimizer and (for
open-ended tasks) the judge — with no Python package and no API key required.

<!-- Full guided workflow added in Task 10. -->
```

- [ ] **Step 2: Verify frontmatter parses and has required fields**

Run:
```bash
python3 -c "
import re,sys
t=open('skills/promptfit/SKILL.md').read()
m=re.match(r'^---\n(.*?)\n---\n', t, re.S); assert m, 'no frontmatter'
fm=m.group(1)
assert re.search(r'^name:\s*promptfit\s*$', fm, re.M), 'name'
assert re.search(r'^description:\s*\S', fm, re.M), 'description'
print('OK')
"
```
Expected: `OK`

- [ ] **Step 3: Commit**

```bash
git add skills/promptfit/SKILL.md
git commit -m "feat: add SKILL.md skeleton"
```

---

### Task 6: `references/optimizer-prompt.md`

**Files:**
- Create: `skills/promptfit/references/optimizer-prompt.md`

The PE-agent system prompt, adapted from prompt-forge's `DEFAULT_OPTIMIZER_PROMPT`. Must instruct:
analyze every example; find gaps vs the current prompt; produce an improved prompt that is additive
(never drop prior rules unless wrong), specific/concrete, well-structured; and emit exactly three
XML sections `<optimized_prompt>`, `<learnings>`, `<issues>`.

- [ ] **Step 1: Write the file**

```markdown
# Optimizer prompt (the "Prompt Engineering agent")

Use this as the instruction set for the optimizer step. Given the current prompt, a training batch
(input → expected output), and the training log, produce an improved prompt.

---

You are an expert Prompt Engineer. Analyze examples of a task and produce the best possible system
prompt enabling an AI agent to perform it accurately and consistently.

You are given: (1) the current system prompt, (2) a training log of what earlier iterations learned,
(3) a batch of input → expected-output examples, (4) optionally, evaluation feedback on failures.

Do this:
1. Analyze every example for patterns, rules, and edge cases.
2. Compare examples against the current prompt to find gaps (uncovered, wrong, or ambiguous).
3. Produce an IMPROVED prompt that is: detailed and specific; covers all patterns found so far;
   addresses every failure; well-structured; unambiguous.

CRITICAL RULES:
- NEVER remove rules from the current prompt unless they are wrong — it holds prior learnings.
- ADD new rules/edge cases from the new examples. REFINE existing rules the examples show need it.
- Prefer concrete rules over vague guidance.
  Bad: "Pay attention to the format." Good: "`urgency` must be low|medium|high; a stated deadline
  within 24h ⇒ high."

Respond with EXACTLY these three tags and nothing outside them:

<optimized_prompt>
The full improved system prompt.
</optimized_prompt>

<learnings>
2–5 bullets: what new rules/patterns this batch revealed (what was learned, not how the text changed).
</learnings>

<issues>
Bullets: anything unresolved — missing info, contradictory examples, edge cases needing more data,
or points needing human clarification. Write "None" if there are none.
</issues>
```

- [ ] **Step 2: Verify the three required tags are present**

Run:
```bash
grep -q '<optimized_prompt>' skills/promptfit/references/optimizer-prompt.md \
 && grep -q '<learnings>' skills/promptfit/references/optimizer-prompt.md \
 && grep -q '<issues>' skills/promptfit/references/optimizer-prompt.md && echo OK
```
Expected: `OK`

- [ ] **Step 3: Commit**

```bash
git add skills/promptfit/references/optimizer-prompt.md
git commit -m "feat: add optimizer-prompt reference"
```

---

### Task 7: `references/evaluators.md`

**Files:**
- Create: `skills/promptfit/references/evaluators.md`

- [ ] **Step 1: Write the file**

````markdown
# Evaluators

Each iteration has two halves. **Inference** (run the candidate prompt on inputs → outputs) is ALWAYS
Claude-native and in-context: apply the candidate system prompt to each eval input and write the
result to `outputs/<stem>.<ext>`. **Scoring** compares those outputs to the expected files.

## Choosing an evaluator (auto-detect, then confirm with the user)

1. If expected outputs parse as JSON objects for ≥50% of examples → **`json_field`**.
2. Else if expected outputs are short (≤ ~5 tokens) exact strings/labels → **`exact`**.
3. Else if the task is extractive with longer text answers → **`token_f1`**.
4. Else (summaries, tone, open-ended judgment) → **`llm_judge`**.

Always state the pick and let the user override.

## Deterministic evaluators (`exact`, `json_field`, `token_f1`)

Copy `score.py` (bundled next to this file) into the project dir. Each iteration:
- write model outputs to `outputs/` (stems matching the expected files),
- run: `python3 score.py --mode <mode> --pred outputs/ --gold <expected_dir>`,
- read the printed JSON's `mean` as the score, and `per_example` to see which cases fail
  (feed failing cases into the next optimizer step as evaluation feedback).

`json_field` = fraction of gold top-level keys whose value matches. `token_f1` = multiset token F1.
These are exact and reproducible — do NOT eyeball matches when a deterministic mode applies.

If Python 3 is unavailable, score inline yourself using the SAME definitions, and tell the user this
run is less reproducible.

## LLM-as-judge (`llm_judge`)

For open-ended tasks. Write a `rubric.md` in the project dir once, then reuse it every iteration so
scoring is consistent. Rubric template:

```markdown
# Scoring rubric
Score each output in [0,1] against the expected output on:
- Correctness of the key content (0.6)
- Completeness — nothing important missing (0.2)
- Format/faithfulness — no invented facts, follows required shape (0.2)
Return the weighted sum. Be strict and consistent; identical quality ⇒ identical score across runs.
```

Judge each eval example against its expected output with this rubric; the score is the mean over the
eval set. Judging costs tokens (counts double in the cost estimate — see `loop-spec.md`).
````

- [ ] **Step 2: Verify the four modes are documented**

Run:
```bash
for m in exact json_field token_f1 llm_judge; do grep -q "$m" skills/promptfit/references/evaluators.md || { echo "missing $m"; exit 1; }; done; echo OK
```
Expected: `OK`

- [ ] **Step 3: Commit**

```bash
git add skills/promptfit/references/evaluators.md
git commit -m "feat: add evaluators reference"
```

---

### Task 8: `references/loop-spec.md`

**Files:**
- Create: `skills/promptfit/references/loop-spec.md`

- [ ] **Step 1: Write the file**

````markdown
# Loop spec

## Split (adaptive, seeded)
- Count examples N. Choose a fixed seed (default 42) and record it.
- N ≥ 15: **train/val/test** = 60/20/20. Score the best prompt once on **test** at the very end.
- N < 15: **train/val** only (no test). Tell the user plainly: "Too few examples for a meaningful
  held-out test; reporting validation score only — treat it as optimistic." Offer test if they insist.
- Persist the assignment to `split.json`: `{"seed":42,"train":[...ids],"val":[...ids],"test":[...ids]}`.
- val and test must never be shown to the optimizer.

## The training loop
Defaults: `batch_size=5`, `max_iterations=20`, `patience=3`, `min_improvement=0.01` (all user-settable).

```
score_current = eval(current_prompt, val)          # ONE pass; then carried forward
best = (v0, score_current)
no_improve = 0
for i in 1..max_iterations:
    batch       = sample(train, batch_size, seed+i)   # sampled from TRAIN only
    result      = optimize(current_prompt, batch, training_log)   # optimizer-prompt.md
    prompt2     = result.optimized_prompt
    score_after = eval(prompt2, val)
    if score_after >= score_current + min_improvement:
        save prompt_v{n}.md
        current_prompt = prompt2 ; score_current = score_after ; no_improve = 0
        if score_after > best.score: best = (v{n}, score_after)
    else:
        no_improve += 1                # current_prompt and its score are unchanged
    append_training_log(i, result.learnings, result.issues, score_before=score_current, score_after, batch_ids, accepted)
    if no_improve >= patience: break   # early stop
# end
if test exists: best.test_score = eval(best.prompt, test)
write report.md
```

**Carry-score-forward:** run exactly ONE fresh val-inference pass per iteration (the candidate). An
accepted candidate's `score_after` becomes the next `score_current`. A rejected candidate leaves
`current_prompt` and its known score intact. Never re-score the unchanged current prompt.

**A rejected iteration must never overwrite a saved `prompt_v*.md`.**

## Optimizer output parsing
Parse `<optimized_prompt>`, `<learnings>`, `<issues>`. If `<optimized_prompt>` is missing/empty, keep
the previous version, log the malformation, and retry the optimizer once. If `<issues>` is "None",
record no issues.

## Consolidation (optional, explicit, never automatic)
When the prompt has grown large or scores plateaued, offer to consolidate: merge redundant/overlapping
rules while preserving every distinct rule; save as a new `prompt_v{n}.md` marked `[CONSOLIDATION]` in
the log. History stays intact.

## Pre-flight cost estimate (show BEFORE training)
```
example_runs ≈ max_iterations × |val| × (2 if llm_judge else 1)   (+ |test| once)
est_tokens   ≈ example_runs × avg_example_tokens + max_iterations × (avg_prompt + batch) tokens
```
Estimate `avg_example_tokens` as chars/4 over the loaded examples. Show `example_runs` and `est_tokens`.

**Budget trigger (default = token estimate):** if `est_tokens > 1_000_000` (user-overridable), warn and
offer: reduce val size, fewer iterations, switch to a deterministic evaluator, or **graduate** to the
prompt-forge library / DSPy / GEPA (see `lineage.md`). This is the only place the graduate pointer
fires at runtime. Proceed only after the user confirms.
````

- [ ] **Step 2: Verify key knobs and the budget number are present**

Run:
```bash
for s in "batch_size=5" "max_iterations=20" "patience=3" "1_000_000" "Carry-score-forward" "split.json"; do
  grep -q "$s" skills/promptfit/references/loop-spec.md || { echo "missing $s"; exit 1; }; done; echo OK
```
Expected: `OK`

- [ ] **Step 3: Commit**

```bash
git add skills/promptfit/references/loop-spec.md
git commit -m "feat: add loop-spec reference"
```

---

### Task 9: `references/lineage.md`

**Files:**
- Create: `skills/promptfit/references/lineage.md`

Draw content from `docs/research-notes.md`. Keep the `[CITATION NEEDED]` placeholder for the user's
2025 paper.

- [ ] **Step 1: Write the file**

```markdown
# Lineage & honest positioning

**What this is.** LLM-as-optimizer *textual gradient descent*: an optimizer LLM reads labeled examples
and rewrites the prompt; candidates are accepted/rejected on a validation score. PromptFit is **not a
new method** — it is a member of a well-established family.

**Prior art (name it honestly).**
- **ProTeGi / APO** — "Automatic Prompt Optimization with 'Gradient Descent' and Beam Search" (EMNLP
  2023) — the closest methodological ancestor.
- **TextGrad**, **OPRO**, **GEPA** — sibling LLM-as-optimizer / reflective methods.
- **DSPy / MIPROv2** — the Bayesian-optimization cousin (Optuna TPE over instructions + demos).
- **PLD (Prompt-Level Distillation)** — distills a teacher into the *system prompt* vs weights; the
  academic twin of "the prompt is the model."
- The 2025 paper PromptForge was based on: **[CITATION NEEDED — fill in]**.

**Already-occupied niches.** Anthropic's first-party `skill-creator` (Improve mode), plus GEPA /
Microsoft SkillOpt / community `prompt-optimizer` skills — all optimize *an agent's own `skill.md`*.

**What PromptFit does differently.** Trains a **portable, provider-agnostic system prompt as the
deliverable** from *your* labeled input→output data, with explicit **train/val/test**, eval-scored
accept/reject, versioning, and **flexible ingestion** (bring data however it is). The value is the
rigor and the portable artifact — not novelty.

## When to graduate — and to what
Move to the **prompt-forge** library (or DSPy/GEPA) when you need: large datasets with cheap
reproducible re-runs (caching), binary inputs (PDF/image/docx), RAG-matched evaluation, DB storage, or
strict token budgeting. PromptFit is tuned for small-to-mid labeled sets where a Claude-native loop shines.
```

- [ ] **Step 2: Verify the placeholder and key names are present**

Run:
```bash
for s in "CITATION NEEDED" "ProTeGi" "MIPROv2" "skill-creator" "graduate"; do
  grep -q "$s" skills/promptfit/references/lineage.md || { echo "missing $s"; exit 1; }; done; echo OK
```
Expected: `OK`

- [ ] **Step 3: Commit**

```bash
git add skills/promptfit/references/lineage.md
git commit -m "feat: add lineage/positioning reference"
```

---

### Task 10: SKILL.md full guided workflow

**Files:**
- Modify: `skills/promptfit/SKILL.md` (replace the `<!-- Full guided workflow added in Task 10. -->` line)

- [ ] **Step 1: Replace the placeholder comment with the workflow body**

Append (replacing the placeholder comment) this content:

````markdown
## How to run this skill

Follow these steps in order. Read the referenced files with the Read tool when you reach them; do not
inline their full contents up front. Keep everything the user produces as plain files under a project
directory they choose (default `./<project-name>/`).

### 0. Frame
Give a 3-line explanation: PromptFit trains a portable system prompt from labeled examples via an
iterative loop (train/val/test, accept/reject, early stopping); it is an LLM-as-optimizer method, not
novel; see `references/lineage.md`. Do NOT detect or require any library.

### 1. Set up the project
Ask for the task/domain in one or two sentences and a seed prompt (offer to draft a basic one). Create
the project dir; write `context.md`, `prompt_v0.md` (the seed), and `LINEAGE.md` (copy the summary from
`references/lineage.md`, including the `[CITATION NEEDED]` line).

### 2. Load examples (flexible ingestion)
Ask where the labeled examples are. Inspect the path and recognize the layout: one subdir per example;
two parallel folders (`inputs/` + `expected/`) matched by filename; paired files by stem; a JSONL/CSV
with input/output columns; or a markdown table. Heuristic: names/columns containing
`expected`/`output`/`label`/`gold` are ground truth; the rest are input(s); multiple input roles are
allowed. **Always confirm the detected mapping and example count with the user before continuing.**
On ambiguity or missing ground truth, stop and ask — never guess.

### 3. Split
Apply the adaptive, seeded split in `references/loop-spec.md`; write `split.json`.

### 4. Pick the evaluator
Auto-detect per `references/evaluators.md`; state the choice; let the user override. For deterministic
modes, copy `references/score.py` into the project. For `llm_judge`, write `rubric.md`.

### 5. Pre-flight cost estimate
Compute and show `example_runs` and `est_tokens` from `references/loop-spec.md`. If over the budget
(default 1,000,000 tokens), warn and offer the adjustment/graduate options. Proceed only on confirmation.

### 6. Train
Run the loop exactly as specified in `references/loop-spec.md`, using `references/optimizer-prompt.md`
for the optimizer step and `references/evaluators.md` for scoring. Each iteration, show: iteration
number, `score_before → score_after`, accepted/rejected, and the learnings. Save accepted versions as
`prompt_v{n}.md`; append every iteration to `training_log.md`.

### 7. Review
Report the best version, the score trajectory, accumulated learnings, and open issues. If a test set
exists, score the best prompt once on it and report that as the unbiased number.

### 8. Consolidate (optional)
If the prompt grew large or plateaued, offer consolidation per `references/loop-spec.md`.

### 9. Deploy / run
The deliverable is `prompt_v{best}.md` — a system prompt usable with any provider. Offer to run it on a
fresh input the user provides, as a final check. Write `report.md` summarizing versions, scores, and
open issues.

## Guardrails
- A rejected iteration must never overwrite a saved `prompt_v*.md`.
- Never show val/test examples to the optimizer.
- If the optimizer output lacks `<optimized_prompt>`, keep the previous version, log it, retry once.
- Prefer deterministic scoring when it applies; do not eyeball matches.
- State honestly when data is too small for a held-out test.
````

- [ ] **Step 2: Verify all referenced files exist and are linked**

Run:
```bash
cd skills/promptfit
for f in references/optimizer-prompt.md references/evaluators.md references/loop-spec.md references/lineage.md references/score.py; do
  test -f "$f" || { echo "missing $f"; exit 1; }
  grep -q "$(basename $f)" SKILL.md || { echo "SKILL.md does not reference $f"; exit 1; }
done; echo OK; cd - >/dev/null
```
Expected: `OK`

- [ ] **Step 3: Commit**

```bash
git add skills/promptfit/SKILL.md
git commit -m "feat: complete SKILL.md guided workflow"
```

---

### Task 11: Repo self-check script + end-to-end smoke note

**Files:**
- Create: `scripts/validate.sh`

- [ ] **Step 1: Write `scripts/validate.sh`**

> ⚠️ **Superseded post-implementation** — the shipped `scripts/validate.sh` also validates
> `marketplace.json`, adds a `trap` cleanup, a partial-credit assertion, and a subdir-guard regression
> test. Treat the shipped file as source of truth.

```bash
#!/usr/bin/env bash
# Static self-check for the promptfit plugin repo. Does NOT run the LLM loop.
set -euo pipefail
cd "$(dirname "$0")/.."

python3 -c "import json; json.load(open('.claude-plugin/plugin.json')); print('plugin.json OK')"

python3 - <<'PY'
import re
t=open('skills/promptfit/SKILL.md').read()
m=re.match(r'^---\n(.*?)\n---\n', t, re.S); assert m, 'no frontmatter'
assert re.search(r'^name:\s*promptfit\s*$', m.group(1), re.M), 'name'
assert re.search(r'^description:\s*\S', m.group(1), re.M), 'description'
print('SKILL.md frontmatter OK')
PY

for f in optimizer-prompt.md evaluators.md loop-spec.md lineage.md score.py; do
  test -s "skills/promptfit/references/$f" || { echo "missing/empty $f"; exit 1; }
done
echo "references OK"

python3 -c "
import json,glob
fs=sorted(glob.glob('examples/ex*/expected_output.json'))
assert len(fs)==12,len(fs)
for f in fs: json.load(open(f))
print('examples OK', len(fs))
"

# score.py self-test on a fixture
tmp=$(mktemp -d); mkdir -p "$tmp/pred" "$tmp/gold"
printf '{"a":1,"b":2}' > "$tmp/gold/x.json"; printf '{"b":2,"a":1}' > "$tmp/pred/x.json"
out=$(python3 skills/promptfit/references/score.py --mode json_field --pred "$tmp/pred" --gold "$tmp/gold")
echo "$out" | grep -q '"mean": 1.0' || { echo "score.py self-test FAILED: $out"; rm -rf "$tmp"; exit 1; }
rm -rf "$tmp"; echo "score.py OK"

echo "ALL CHECKS PASSED"
```

- [ ] **Step 2: Make executable and run it**

Run:
```bash
chmod +x scripts/validate.sh && ./scripts/validate.sh
```
Expected: ends with `ALL CHECKS PASSED`

- [ ] **Step 3: Commit**

```bash
git add scripts/validate.sh
git commit -m "test: add repo self-check script"
```

- [ ] **Step 4: Manual end-to-end smoke test (record result, do not automate)**

In a fresh Claude Code session rooted at `~/Repo/promptfit` with the skill installed: run `/promptfit`,
point it at `examples/`, and confirm it (a) detects the one-subdir-per-example layout and asks to
confirm, (b) writes `split.json`, (c) shows a pre-flight estimate, (d) runs ≥2 iterations accepting at
least one improvement, (e) writes `prompt_v*.md`, `training_log.md`, `report.md`, `LINEAGE.md`, and
(f) runs the trained prompt on a new email. Note any deviations as follow-up issues.

---

## Self-review (completed by plan author)

**Spec coverage:** setup/context/seed (T5,T10 §1) · flexible ingestion+confirm (T10 §2) · adaptive
seeded split (T8,T10 §3) · evaluator auto-select + score.py + judge rubric (T4,T7,T10 §4) · pre-flight
token budget ~1M (T8,T10 §5) · Claude-native loop with optimizer step, accept/reject, patience,
carry-forward (T6,T8,T10 §6) · review + held-out test (T10 §7) · consolidation (T8,T10 §8) · deploy/run
(T10 §9) · lineage + [CITATION NEEDED] (T9) · plugin packaging (T1) · README/install (T2) · smoke
dataset (T3) · validation (T11). All spec sections map to a task.

**Placeholder scan:** the only intentional placeholder is `[CITATION NEEDED]` (user-supplied, tracked
in the spec's Open items). No TBD/TODO/"handle edge cases" left in steps.

**Type/name consistency:** `score.py` modes `exact|json_field|token_f1` used identically in T4, T7, T11;
files `prompt_v{n}.md`, `split.json`, `training_log.md`, `report.md`, `outputs/`, `context.md`,
`LINEAGE.md` named identically across tasks; the three optimizer tags match between T6 and T8.
```
