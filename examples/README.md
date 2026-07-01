# Example dataset — support-email extraction

12 labeled examples. Layout: one folder per example, `input.txt` (a short support email) +
`expected_output.json`. Schema (all keys required):

- `intent`: one of `refund`, `cancel`, `technical`, `billing`, `praise`, `other`
- `product`: the product mentioned, or `null`
- `urgency`: `low`, `medium`, or `high`
- `wants_refund`: boolean

Used as PromptFit's smoke test: `/promptfit` should ingest this folder, split, train, and produce
a prompt that maps an email to this JSON. Deterministic evaluator = `json_field`.
