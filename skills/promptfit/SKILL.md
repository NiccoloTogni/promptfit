---
name: promptfit
description: Fit a portable system prompt to labeled input→output examples via an iterative ML loop — seeded train/val/test split, an optimizer step that rewrites the prompt from a batch plus accumulated learnings, eval-scored accept/reject, and early stopping. Use when someone wants to "learn", "optimize", "distill", or "train" a reusable system prompt from labeled examples (extraction, classification, structured-output tasks) rather than tune an agent's own skill.md. Not for editing this agent's behavior.
---

# PromptFit

Train a portable, provider-agnostic **system prompt** from labeled `input → expected_output` examples.
The trained prompt is the deliverable. This runs Claude-native — Claude is the optimizer and (for
open-ended tasks) the judge — with no Python package and no API key required.

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
modes, copy `references/score.py` into the project and build the flat, id-keyed `gold/` directory it
requires (see `references/evaluators.md` — `score.py` ignores subdirectories and matches by filename
stem). For `llm_judge`, write `rubric.md`.

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
