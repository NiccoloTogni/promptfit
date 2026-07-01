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

**Outputs hygiene:** clear `outputs/` at the start of every iteration before writing the candidate's
predictions, so a stale file from a prior iteration is never silently rescored. `score.py` requires a
flat, id-keyed `gold/` + `outputs/` layout (stems = example ids) — see `references/evaluators.md`, and
always check its reported `n`/`warnings` before trusting the mean.

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
