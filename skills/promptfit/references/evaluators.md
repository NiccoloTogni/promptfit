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
