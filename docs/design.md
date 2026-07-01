# PromptFit — Design Spec

- **Date:** 2026-07-01
- **Status:** Implemented & merged to `main` (2026-07-01). Reconciled with the shipped plugin — see
  "Implementation reconciliation" below.
- **Author:** Toni (with Claude)
- **Naming:** the **skill** is **PromptFit** (`/promptfit`). The **library** it optionally graduates
  to is **prompt-forge** (a separate existing Python package). Keep the two distinct throughout.

## Implementation reconciliation (2026-07-01)

The plugin was built from `docs/plan.md` and merged to `main`. A review-driven hardening pass then
changed a few behaviors from this original spec. Where this document and the shipped files under
`skills/promptfit/` + `scripts/` disagree, **the shipped files win**; the notes below are folded into
the sections that follow.

- **`marketplace.json` added.** A `.claude-plugin/marketplace.json` catalog ships so `/plugin
  marketplace add <repo>` + `/plugin install` work. (Publishing to a public registry is still out of
  scope — see Non-goals.)
- **Deterministic scoring is a flat, id-keyed contract.** `score.py` matches predictions to gold by
  filename **stem = example id** and reads only flat files (subdirectories are ignored). The workflow
  materializes a flat `gold/` dir and writes `outputs/<id>.<ext>`, clearing `outputs/` each iteration.
  `score.py` reports a `warnings` array (stdout + stderr) on ignored subdirs / missing preds / `n=0`
  and scores an unreadable item `0` instead of crashing — so a layout mismatch can't be mistaken for a
  perfect score. Read `n`/`warnings` before trusting `mean`.
- **`evaluator.md` deliverable dropped.** The chosen evaluator is recorded via the copied `score.py`
  (deterministic) or `rubric.md` (judge) plus the `gold/` dir — there is no separate `evaluator.md`
  file. The ingested data is referenced in place, not necessarily copied into the project dir.

## Summary

A Claude Code **skill** that trains a **portable, provider-agnostic system prompt** from labeled
`input → expected_output` examples using an ML-style iterative loop: seeded train/val/test split,
an optimizer step (an LLM rewrites the prompt from a batch + accumulated learnings), eval-scored
**accept/reject**, and **early stopping**. "The prompt is the model."

It packages the *principles* of the prompt-forge library as a **self-contained** agent workflow —
no Python package and no external API key required for the core path. The prompt-forge library
remains available as an optional "graduate to" upgrade, referenced only in docs.

PromptFit does **not** claim methodological novelty. It is an instance of the well-known
LLM-as-optimizer / *textual gradient descent* family. Its value is (1) **classical-ML rigor**
(train/val/test, eval-scored accept/reject, versioning) applied to prompt training, (2) a
**portable prompt artifact** as the deliverable, and (3) **flexible data ingestion**. This honesty
is baked into the skill (see Positioning).

## Goals

- Train a deployable system prompt from a user's labeled examples, standalone, with zero install.
- Reproduce the prompt-forge loop faithfully but as a **Claude-native mini-loop** (Claude is optimizer
  and, for semantic tasks, judge).
- Be honest and explicit about prior art and what differentiates this from existing tools/skills.
- Ship as an independently installable **Claude Code plugin** in its own repo.

## Non-goals (v1, deferred — with a docs pointer to library mode where relevant)

- Binary inputs (PDF / image / docx) in standalone → recommend the prompt-forge library.
- RAG / web-search retriever parity in standalone (but warn about the eval/production distribution gap).
- SQL storage backends, response caching, custom batch-selection strategies.
- A multi-command/power-user toolkit surface (single guided workflow only).
- Automated detection of, or code-gen hand-off to, the prompt-forge library (explicitly cut — see
  "Library on-ramp").
- Publishing to a public marketplace registry (the repo is plugin-ready and ships a
  `.claude-plugin/marketplace.json` so `/plugin marketplace add <repo>` works; registry publishing is
  out of scope for v1).

## Positioning / prior art (baked into the skill as `lineage.md`)

Stated plainly to the user (3-line summary at step 0) and written into each project's `LINEAGE.md`:

- **What this is:** LLM-as-optimizer *textual gradient descent* — an optimizer LLM reads labeled
  examples and rewrites the prompt; accept/reject on a validation score.
- **Prior art, named:** ProTeGi/APO (EMNLP 2023 — the method's ancestor), TextGrad / OPRO / GEPA
  (siblings), **DSPy / MIPROv2** (the Bayesian-optimization one), and the 2025 paper prompt-forge was
  based on — **[CITATION NEEDED — user to provide]**.
- **Already-occupied niches:** Anthropic's first-party `skill-creator` (Improve mode), and
  GEPA / SkillOpt / community `prompt-optimizer` skills — all of which tune *an agent's own skill.md*.
- **What's different here:** trains a **portable, provider-agnostic system prompt as the deliverable**
  from *your* labeled data, with explicit train/val/test + eval-scored accept/reject + versioning, and
  **flexible ingestion** (bring data however it is). Not novel as a method; the value is the rigor and
  the portable artifact.

## Distribution

- Its own small repo (`promptfit`), packaged as a **Claude Code plugin**.
- Install: add the marketplace → `/plugin install`, or copy `skills/promptfit/` into `~/.claude/skills/`.
- The prompt-forge library repo gets a README link pointing to this skill repo.

## Repo layout

```
promptfit/                              # standalone, independently installable
├── .claude-plugin/
│   ├── plugin.json                     # plugin manifest: name, version, description, author
│   └── marketplace.json                # marketplace catalog so `/plugin marketplace add` works
├── skills/
│   └── promptfit/
│       ├── SKILL.md                    # entry: trigger + guided workflow
│       └── references/
│           ├── optimizer-prompt.md     # the "PE agent" prompt (learnings/issues, additive)
│           ├── evaluators.md           # exact / JSON-field / token-F1 / LLM-judge recipes
│           ├── loop-spec.md            # exact loop: split, accept/reject, patience, carry-forward
│           ├── lineage.md              # prior art + differentiation + "when to graduate"
│           └── score.py                # stdlib deterministic scorer (copied into each project)
├── examples/                           # bundled smoke-test dataset (12 labeled examples)
├── scripts/
│   └── validate.sh                     # repo self-check (no LLM loop)
├── docs/
│   └── design.md                       # this spec
└── README.md                           # what it is + install
```

`SKILL.md` frontmatter `description` is trigger-focused, e.g.: *"Fit a portable system prompt to your
labeled input→output examples via an iterative ML loop — train/val/test split, eval-scored
accept/reject, early stopping. Use when someone wants to 'learn' / 'optimize' / 'distill' / 'train' a
prompt from labeled examples rather than tune an agent's own skill.md."*

## The guided workflow (`SKILL.md`)

One progressive flow. Everything the user keeps is plain files under a chosen project dir.

0. **Frame** — 3-line explanation of the method + surfaced lineage note. (No library detection.)
1. **Set up project** — capture task context + a seed prompt (generate a basic one if none); create
   the project dir; write `context.md`, `prompt_v0.md`, `LINEAGE.md`.
2. **Load examples** — flexible ingestion (see below); validate and **confirm the detected mapping**
   before continuing; report count.
3. **Split** — seeded **train/val/test** (adaptive; see below); persist per-set IDs + seed.
4. **Pick evaluator** — auto-detect (exact / JSON-field / token-F1 / LLM-judge), user-overridable;
   record choice; generate `score.py` for deterministic evaluators or `rubric.md` for the judge.
5. **Pre-flight estimate** — show the cost estimate + budget check (see below); user proceeds or adjusts.
6. **Train (the loop)** — iterate (see Loop); show per-iteration scores, accept/reject, learnings.
7. **Review** — best version + score trajectory + accumulated learnings + open issues; if the set is
   large enough, score the best prompt **once on the held-out test set** for an unbiased number.
8. **Consolidate (optional)** — if the prompt grew large or plateaued, offer the merge-redundant-rules
   step → new version.
9. **Deploy/run** — the deliverable is `prompt_vN.md`; show how to use it as a system prompt anywhere,
   and offer to run it on a fresh input now.

## Standalone execution model

### Flexible ingestion
Claude reads the data directly, so it adapts to the user's layout, then **confirms before training**:
- Layouts recognized: one subdir per example (`input.* + expected_output.*`); two parallel folders
  (`inputs/` + `expected/`) matched by filename; paired files by stem (`001.in.txt` / `001.out.json`);
  a single **JSONL/CSV** with input/output columns; a table in a markdown file.
- Default heuristic: names/columns containing `expected` / `output` / `label` / `gold` → ground truth;
  the rest → input(s). Multiple input roles allowed (e.g. `email` + `attachment`).
- Ambiguity or missing ground truth → stop and confirm; never guess silently.

### Evaluators
Each iteration has two halves, handled differently:
- **Inference** (run the candidate prompt on inputs → outputs): **always Claude-native, in-context.**
  No API key, no code. Outputs written to `outputs/`. This is the token cost driver.
- **Scoring** (outputs vs expected):
  - **Deterministic** (exact / JSON-field / token-F1): copy the stdlib **`score.py`** into the project
    at setup and run it via Bash each iteration. It matches predictions to gold by filename **stem =
    example id** over **flat** dirs (subdirs ignored), so build a flat `gold/` dir and write
    `outputs/<id>.<ext>`, clearing `outputs/` each iteration. It reports `mean`, `per_example`, and a
    `warnings` array (ignored subdirs / missing preds / `n=0`) and scores unreadable items `0` rather
    than crashing — check `n`/`warnings` before trusting `mean`. Reproducible, cheap, exact.
  - **LLM-as-judge** (open-ended/semantic): **Claude is the judge**, scoring against a written
    `rubric.md` for cross-iteration consistency. No code; costs tokens.
- "No install" = no pip packages and no external API key, but the ambient Python/bash of the Claude
  Code session is used for `score.py`. If Python is absent, deterministic scoring falls back to careful
  inline scoring, **flagged as less reproducible**.

### The loop
```
split -> train / val / test (seeded, persisted)
score_current = eval(current_prompt, val)          # one pass, then carried forward
for i in 1..max_iterations:
    batch          = sample(train, batch_size)
    prompt'        = optimize(current_prompt, batch, training_log)   # Claude, per optimizer-prompt.md
    score_after    = eval(prompt', val)
    if score_after >= score_current + min_improvement:
        accept: save prompt_v{n}.md; current_prompt = prompt'; score_current = score_after
    else:
        reject: keep current_prompt (and its known score)
    append to training_log.md (learnings, issues, scores, batch IDs, accept/reject)
    early-stop if `patience` consecutive non-accepts
save best version + report.md
```
- **Carry the score forward:** only **one** fresh val-inference pass per iteration (the candidate).
  An accepted candidate's `score_after` becomes the next `score_current`; a reject leaves the current
  prompt's known score intact.
- **Optimizer step** mirrors the prompt-forge `DEFAULT_OPTIMIZER_PROMPT`: additive (never drop prior
  rules unless wrong), emits an improved prompt + `learnings` + `issues`, prefers concrete rules.
- Defaults follow the library's spirit: `batch_size=5`, `max_iterations=20`, `patience=3`,
  `min_improvement` small and configurable.

### Adaptive train/val/test
- **≥ ~15–20 examples:** full train/val/test (default 60/20/20); test scored once at the end.
- **Below that:** train/val only, stated plainly — *"Too few examples for a meaningful held-out test;
  reporting validation score only — treat it as optimistic."* Test offered if the user insists.
- Split IDs + seed always persisted for reproducibility.

### Pre-flight cost estimate & budget trigger
There is **no external reference** for "oversized"; cost is fully determined by config. Before training,
show:
```
example_runs ≈ max_iterations × |val| × (2 if LLM-judge else 1)   (+ |test| once)
est_tokens   ≈ example_runs × avg_example_tokens + max_iterations × (prompt + batch) tokens
```
- Default **budget trigger = token estimate**: warn when `est_tokens` exceeds a soft default (~1M),
  **user-overridable**. Mirrors the prompt-forge `max_total_tokens` knob.
- On trip, the message offers: reduce val / fewer iterations / switch to deterministic eval / consider
  the prompt-forge library or DSPy/GEPA (the only place the "graduate" pointer fires at runtime).

### Consolidation
Explicit, optional, user-triggered (never automatic). Merges redundant/overlapping rules while
preserving distinct coverage; saved as a new version; history stays intact.

### Deploy / run
Deliverable is `prompt_vN.md` — usable as a system prompt with any provider. The skill offers to run
the trained prompt on a fresh input immediately as a final check.

## Deliverable artifacts (per project dir)

```
<project>/
├── context.md            # task/domain context
├── LINEAGE.md            # provenance: method, prior art, differentiation (from lineage.md)
├── split.json            # train/val/test IDs + seed
├── score.py / rubric.md  # chosen evaluator: copied score.py (deterministic) or rubric.md (judge)
├── gold/                 # flat, id-keyed expected outputs (<id>.<ext>) for deterministic scoring
├── prompt_v0.md … prompt_vN.md   # version history (accepted versions only)
├── outputs/              # per-iteration model outputs (cleared each iteration; for scoring/repro)
├── training_log.md       # per-iteration learnings, issues, scores, batch IDs, accept/reject
└── report.md             # summary: best version, score trajectory, test score, open issues
```

## Reference files (content outline)

- **optimizer-prompt.md** — the PE-agent system prompt (adapted from prompt-forge's
  `DEFAULT_OPTIMIZER_PROMPT`): additive rule preservation, `learnings`/`issues` output, concrete-rule bias.
- **evaluators.md** — recipes + selection heuristic for exact / JSON-field / token-F1 / LLM-judge,
  including the `score.py` templates and the judge `rubric.md` template.
- **loop-spec.md** — the exact loop above (split, accept/reject, carry-forward, patience, consolidation),
  defaults, and the pre-flight cost formula.
- **lineage.md** — the Positioning section, plus "when to graduate — and to what."
- **score.py** — stdlib deterministic scorer (`exact` / `json_field` / `token_f1`); flat id-keyed
  pred/gold matching, `warnings` output + graceful per-item degradation. Copied into each project.

## Error handling & edge cases

- No/blank ground-truth roles or ingestion ambiguity → stop and confirm mapping (never guess).
- Too few examples → adaptive split + explicit warning.
- Malformed optimizer output (missing rewritten prompt) → keep previous version, log, retry once.
- No accepted improvement for `patience` iterations → early stop; report best-so-far honestly.
- Python absent → deterministic scoring falls back to careful inline scoring, flagged.
- Deterministic scoring layout mismatch (unflattened data, missing/extra files) → `score.py` emits
  `warnings` + a small `n`, never silently reporting success. Unreadable output file → that item scores
  `0`, run continues (exit 0).
- Estimate over budget → pre-flight warning with adjustment options + graduate pointer.
- Rejected iterations must never overwrite the best version.

## Validation / testing

- Bundled **example dataset** (~12-example text or JSON-extraction task) in `examples/`.
- Manual acceptance run: fresh session → invoke skill → confirm it ingests, confirms mapping, splits,
  runs ≥2 iterations, accepts an improvement, writes `prompt_vN.md` + `training_log.md` + `report.md`
  + `LINEAGE.md`, and runs the trained prompt on a new input.
- Assertions: split is seeded/reproducible; `score.py` runs deterministically; a rejected iteration
  leaves the best version untouched; pre-flight estimate is shown before any spend.

## Open items

- **2025 paper citation** for `lineage.md` / `LINEAGE.md` — user to provide (marked `[CITATION NEEDED]`).
