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
