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

Copy `score.py` (bundled next to this file) into the project dir.

**One-time: build a flat, id-keyed gold directory.** `score.py` matches predictions to gold by
FILENAME STEM, and the stem IS the example id. It reads only flat files (subdirectories are ignored).
So whatever the ingestion layout was (one subdir per example, parallel folders, JSONL/CSV, a table),
first materialize a flat `gold/` dir with one file per example named `<id>.<ext>` (e.g.
`gold/ex04.json`), using the split ids as the stems.

Each iteration:
- **clear `outputs/` first** — a stale file from a prior iteration would otherwise be silently rescored,
- write this candidate's outputs to `outputs/<id>.<ext>`, stems matching the gold files,
- run: `python3 score.py --mode <mode> --pred outputs/ --gold gold/`,
- **check `n` and `warnings` before trusting `mean`** — `n` must equal the number of eval examples and
  `warnings` must be empty. A non-empty `warnings` (or a surprisingly small `n`) means the directories
  didn't line up, not that the prompt is good or bad — fix the layout and re-run.
- read `mean` as the score, and `per_example` to see which cases fail (feed failing cases into the next
  optimizer step as evaluation feedback).

`json_field` = fraction of gold top-level keys whose value matches (it does NOT penalize extra keys the
prediction adds beyond the gold ones). `token_f1` = multiset token F1 over whitespace-split tokens (so
it is case- and punctuation-sensitive). `exact` = full-string match after trimming. These are exact and
reproducible — do NOT eyeball matches when a deterministic mode applies.

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
