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
