---
name: docs-writing
description: Use when writing, editing, or reviewing user-facing technical documentation prose (guides, reference pages, READMEs, changelogs) — or when prose is called wordy, vague, passive, idiomatic, or hard for non-native speakers to follow.
---

# Docs Writing (Simplified Technical English)

Plain technical prose is a small set of machine-checkable rules plus a few
judgment rules. Automate the checkable ones; spend your thinking on facts
and words. Rules follow ASD-STE100.

## Prose rules

- One idea per sentence. At most 25 words in the main statement, 30 total.
- Active voice, simple present. Imperative mood for steps ("Run X to do
  Y."). No progressive forms ("is building").
- No "may" or "might". "can" for capability or permission, "must" for
  obligation, "will" only for genuine future.
- No idioms or metaphors ("fails loudly", "behind your back"), no "etc.",
  "e.g.", "i.e.", "&", "let's", or contractions.
- Articles ("a", "the") are mandatory. Address the reader as "you".
- One term, one meaning. Never alternate synonyms for variety.

Before/after:

- "Freshly published versions are refused by a cooldown window until they
  have had time to be noticed." → "A cooldown window rejects new
  versions. The delay gives you time to notice a problem."
- "The kernel is not installed with the binary." → "The installer does not
  install the kernel."
- "A stale lock is detected by re-hashing the file." → "Rig re-hashes the
  file to detect a stale lock."

## Rewriting without moving facts

A style pass must not change facts:

- Code fences, tables, headings, and link URLs stay byte-identical; never
  re-wrap a line inside an inline code span.
- Verify against git: diff fences, table rows, and URLs against
  `git show HEAD:<file>`, and compare inline-code spans as normalized
  multisets.
- Active voice needs an actor; naming the wrong one flips a fact ("the
  plan is baked into the jar" — the *build* command does it, not
  *launch*). Re-read every sentence whose actor changed.
- From given facts, state only those facts. Do not invent mechanisms or
  failure behavior ("the command fails with a hint") to fill gaps.

## Checker

Run the skill's own script, verbatim, from anywhere:

    python3 ~/.agents/skills/docs-writing/scripts/check-docs-english.py docs/

Pass any file or directory instead of `docs/`. Do not copy or adapt it
into the project. It reports per-file clean rates and exits non-zero
below the threshold (default 80%, override `--threshold`). It flags
sentence length, modals, progressives, passive voice, and banned
phrasings; `docs/index.md` is exempt by design. Known traps it already
handles, and rules for any future fix:

- Each list item is its own block; never "fix" that by merging items.
- A possessive `'s` is not a contraction; only real contractions count.
- `be`-verb false positives ("is missing", "is nothing", "is then") are
  whitelisted. On a new false positive, fix this script's whitelist —
  never mangle prose to satisfy the checker, and never edit a copy.

## Where the rules bend

Editorial sections (homepages, "Why X") are exempt — check around them
by passing explicit file paths. `docs/index.md` is already exempt.
Confirm exemptions with your human partner. Changelog entries can use
past tense but stay active. Code, tables, and command output are not
prose.

## Common mistakes

| Mistake | Fix |
|---|---|
| Adjectival passives survive ("the classpath is closed") | "the classpath stays closed" |
| Caveats "simplified" away | Keep every caveat; simplify wording only |
| Checker clean but prose fabricated facts | Re-diff facts against source bullets |
| Prose edited to satisfy a checker false positive | Fix the checker's whitelist instead |
