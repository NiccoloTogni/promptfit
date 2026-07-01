# Sample run — support-email extraction

An illustrative end-to-end run of PromptFit on the bundled [`examples/`](../examples) dataset (12
labeled support emails → a 4-key JSON object). It doubles as the design spec's manual acceptance run.

**Setup**
- Evaluator: `json_field` (deterministic, via `score.py`) — auto-detected from JSON expected outputs.
- Split: seed 42; **N=12 < 15 → train/val only** (no held-out test).
  - train (8): ex01, ex02, ex04, ex05, ex07, ex10, ex11, ex12
  - val (4): ex03, ex06, ex08, ex09
- Pre-flight estimate: ~14k tokens (well under the 1M budget trigger).

**Trajectory (validation score, `json_field`)**

| version | val score | decision | what changed |
|---|---|---|---|
| `prompt_v0` (seed) | 0.875 | baseline | vague prompt: no enum, no urgency rule, no full-product-name rule |
| `prompt_v1` | **1.0** | ✅ accept (≥ +0.01) | fixed ex06 `product` (`Pixel Pro`→`Pixel Pro app`) and ex09 `urgency` (`medium`→`high`) |
| candidate (iter 2) | 1.0 | ❌ reject | val saturated; best version left untouched |

**What the optimizer learned (v0 → v1)**
- `intent` is a fixed enum — list the allowed values and define each.
- `urgency=high` when the issue blocks the customer's work/use, the item is fully broken, or there's a
  deadline within ~24h ("renews tomorrow"); else `medium`; `low` for routine/no-pressure.
- `product` must keep its type word exactly as written ("Nimbus router", "Pixel Pro app").
- `wants_refund=true` only on an explicit money-back ask (refund-for-broken ⇒ true).

**Deliverable check** — the trained prompt on a fresh, unseen email:

> "Our whole team can't log in this morning — the dashboard returns a 500 error and we're completely blocked."

```json
{"intent":"technical","product":null,"urgency":"high","wants_refund":false}
```

**Honesty note.** 1.0 is a **validation** score on a tiny (4-example), saturated set — treat it as
optimistic, not evidence of perfect generalization. With ≥15 labeled examples the run would carry a
held-out **test** number and the optimizer would have more room past this ceiling.

**The trained prompt (`prompt_v1`)**

```
You are a support-email classifier. Given a customer email, output ONLY a JSON object with exactly the
keys `intent`, `product`, `urgency`, and `wants_refund` (no extra keys, no prose).

- `intent`: exactly one of `refund`, `cancel`, `technical`, `billing`, `praise`, `other`.
  - `refund` = asking for money back / to return an item for a refund.
  - `cancel` = asking to cancel an account, plan, or subscription.
  - `technical` = a product/service is broken, crashing, or not working.
  - `billing` = a charge/invoice/payment question or dispute (no refund requested).
  - `praise` = positive feedback / thanks.
  - `other` = anything else (e.g. a general question).

- `product`: the product/plan/app named in the email, written with its type word exactly as it appears
  (e.g. `"Nimbus router"`, `"Aero headphones"`, `"Pixel Pro app"`, `"Vera Plus"`). Use `null` if none.

- `urgency`: one of `low`, `medium`, `high`.
  - `high`: the issue blocks the customer's work or normal use, the product is fully broken/unusable,
    OR there is a stated deadline within ~24h (e.g. "renews tomorrow", "before the next renewal").
  - `medium`: a real problem or dispute that is not blocking and has no imminent deadline.
  - `low`: general questions, praise, or routine requests with no time pressure.

- `wants_refund`: `true` only if the customer asks for money back / a refund; otherwise `false`.
  A `refund` intent for a broken or misdescribed item is `true`.

Output only the JSON object.
```
