---
name: promptfit
description: Fit a portable system prompt to labeled input→output examples via an iterative ML loop — seeded train/val/test split, an optimizer step that rewrites the prompt from a batch plus accumulated learnings, eval-scored accept/reject, and early stopping. Use when someone wants to "learn", "optimize", "distill", or "train" a reusable system prompt from labeled examples (extraction, classification, structured-output tasks) rather than tune an agent's own skill.md. Not for editing this agent's behavior.
---

# PromptFit

Train a portable, provider-agnostic **system prompt** from labeled `input → expected_output` examples.
The trained prompt is the deliverable. This runs Claude-native — Claude is the optimizer and (for
open-ended tasks) the judge — with no Python package and no API key required.

<!-- Full guided workflow added in Task 10. -->
