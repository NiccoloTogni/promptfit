# PromptFit — Prior-art research notes

Captured 2026-07-01 from a deep-research pass (5 angles → 19 sources → 90 claims → 24 verified) plus a
recovered earlier run. Source of truth for `lineage.md`. Some very recent URLs are flagged to
re-verify before public citation.

## Verdict

- **As a method:** *not novel.* PromptFit is a member of the well-established **LLM-as-optimizer /
  textual gradient descent** family. Closest ancestor on method = **ProTeGi/APO**; closest twin on the
  "prompt is the model" framing = **PLD**; the **Bayesian** relative the user remembered = **DSPy/MIPROv2**.
- **As a Claude skill:** the "optimize a prompt" niche is *partly occupied* — including first-party — but
  every occupant tunes **an agent's own `skill.md`/description**, not a portable prompt trained from a
  user's labeled input→output data.
- **PromptFit's differentiation:** portable, provider-agnostic **system-prompt artifact** trained from
  *your* labeled examples with **classical-ML rigor** (train/val/test, eval-scored accept/reject,
  versioning) and **flexible ingestion**. Honest positioning: the value is the rigor + the artifact, not
  a new algorithm.

## Libraries / papers (the family)

| Name | Paradigm | Key source | Relationship |
|---|---|---|---|
| **ProTeGi / APO** — "Automatic Prompt Optimization with 'Gradient Descent' and Beam Search" | Textual "gradients" from labeled minibatches + beam search; nonparametric | EMNLP 2023, aclanthology.org/2023.emnlp-main.494 (arXiv 2305.03495) | **Direct methodological ancestor** |
| **GEPA** | Reflective prompt mutation; accept/reject on val minibatch; accumulated NL lessons; beats MIPROv2; `pip install gepa` + `dspy.GEPA` | arXiv 2507.19457 | **Closest living sibling** (accept/reject + accumulated learnings) |
| **TextGrad** | Backpropagates textual feedback as "gradients" across a compound system | arXiv 2406.07496 (Nature 2025) | Sibling; generalizes beyond prompts |
| **OPRO** — "LLMs as Optimizers" | LLM generates candidates from a meta-prompt of past solutions+scores | arXiv 2309.03409 (DeepMind) | Establishes LLM-as-optimizer paradigm |
| **DSPy** (COPRO / **MIPROv2**) | **Bayesian** (Optuna TPE) search over instructions + few-shot demos | dspy.ai/api/optimizers/MIPROv2/ ; arXiv 2406.11695 | The **Bayesian** one; genuinely different paradigm |
| **PLD — Prompt-Level Distillation** | Distills teacher reasoning into the student's **system prompt** vs weights; non-parametric alt to fine-tuning | arXiv 2602.21103 *(recent — re-verify)* | **Twin of the "prompt is the model" framing** |
| **FAPO** (Cisco) | LLM (Claude Code) as autonomous optimizer; ships as a Claude Code slash-command `/optimization` | github.com/cisco-foundation-ai/fully-automated-prompt-optimization | Agentic prompt-opt packaged for Claude Code |
| **Arize "Prompt Learning"** | 3-model loop: Agent → Evaluator LLM feedback → Meta-Prompt rewrite; applied to system prompts/CLAUDE.md | github.com/Arize-ai/prompt-learning | Same textual-feedback paradigm |

DSPy = MIPRO = Bayesian was independently **confirmed with primary sources** (dspy.ai docs state
"we use Bayesian Optimization…"; implemented via Optuna TPE) in a prior verification run.

## Claude skills already in the space (all tune the agent's own skill.md)

- **Anthropic first-party `skill-creator`** — Create / Eval / **Improve** / Benchmark modes. Improve =
  generate a labeled eval set, split ~60/40 train/held-out, evaluate current description, rewrite it on
  failures (textual gradient descent, first-party). github.com/anthropics/skills ; tessl.io blog.
- **GEPA Prompt Optimizer** skill — mcpmarket.com/tools/skills/gepa-prompt-optimizer-dspy-guide.
- **Microsoft SkillOpt** — text-space optimizer rewriting a single `skill.md` via a separate optimizer
  LLM analyzing trajectories (+25%). medium.com/@tort_mario/how-microsoft-skillopt-…
- **MindStudio self-improving skill** — runs `skill.md` vs `eval.json`, computes pass rate, rewrites,
  repeats. mindstudio.ai blog.
- Community: `affaan-m/everything-claude-code` → `skills/prompt-optimizer`; `optimizing-prompts`;
  `llm-prompt-optimizer` (claudskills.com).

## Caveats

- The deep-research workflow's final synthesis step malfunctioned (returned placeholder data); the above
  is synthesized from its 24 adversarially-verified claims + the 19 cited sources, not its auto-summary.
- Re-open primary URLs before public citation for the most recent items (PLD `2602.21103`; 2026
  marketplace skill pages), since the run's clock sits in mid-2026 and one earlier hallucination (a DSPy
  "Gaussian process" quote) was caught and discarded during verification.

## Open item

- **The 2025 paper PromptForge (the library) was based on** — the user will supply this citation; it is
  the most important primary reference for `lineage.md`. Currently `[CITATION NEEDED]`.
