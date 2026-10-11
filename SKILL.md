---
name: docs-writing
description: Use when writing, editing, or reviewing user-facing technical documentation prose (guides, reference pages, READMEs, changelogs) — or when prose is called wordy, vague, passive, idiomatic, hard for non-native speakers to follow, or AI-sounding (LLM clichés such as "delve", "not just X, but Y", "here is the thing", "experts argue").
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

## LLM clichés

LLM prose has known tells: stock phrasings that carry no fact. The checker
flags them and names the fix. Families: staged reveals ("here is the thing",
"the punchline is", "turns out", "you already know"), negative parallelism
("not just X, but Y", "not X, but Y", "no X, no Y, no Z", "isn't X. It is
Y."), framing and hedging ("it is important to note", "experts argue",
"time will tell", "that is why it mattered", "stands as a testament", "plays
a crucial role"), AI vocabulary ("delve", "seamless", "pivotal",
"meticulous"), promo tone ("boasts", "hidden gem", "in the heart of"), and
chatbot leftovers ("as of my last update"). A fixed sentence states the fact
the tell gestures at. Rephrasing a tell is not fixing it: "time will reveal"
keeps the tell of "time will tell".

Tells the checker cannot see, because they span sentences; never write them:

- Two or more questions in a row ("Do I trust it? Do I use it?").
- Three consecutive sentences opening on the same word ("Maybe X. Maybe Y.
  Maybe Z.").
- Consecutive sentences on the same skeleton ("A reads both. B reads both.").

Colon-into-a-triple ("ports, processes, and state") stays unflagged on
purpose: in reference prose it is usually a real enumeration.

## Checker

Run the skill's own script, verbatim, from anywhere:

    python3 ~/.agents/skills/docs-writing/scripts/check-docs-english.py docs/

Pass any file or directory instead of `docs/`. Do not copy or adapt it
into the project. It reports per-file clean rates and exits non-zero
below the threshold (default 80%, override `--threshold`). It flags
sentence length, modals, progressives, passive voice, banned phrasings, and
LLM clichés; `docs/index.md` is exempt by design. Known traps it already
handles, and rules for any future fix:

- Each list item is its own block; never "fix" that by merging items.
- A possessive `'s` is not a contraction; only real contractions count.
- `be`-verb false positives ("is missing", "is nothing", "is then") are
  whitelisted. On a new false positive, fix this script's whitelist —
  never mangle prose to satisfy the checker, and never edit a copy.

Checker changes are regression-tested: `bash tests/run.sh`.

## Where the rules bend

Editorial sections (homepages, "Why X") are exempt — check around them
by passing explicit file paths. `docs/index.md` is already exempt.
Confirm exemptions with your human partner. Changelog entries can use
past tense but stay active. Code, tables, and command output are not
prose.

Clichés apply everywhere, style rules do not. For exempt prose or an
"remove only the AI tells" request, run the checker with
`--cliches-only`: it checks every file (no exemptions), flags only
clichés, and leaves voice, contractions, and sentence shapes alone. Fix
only the flagged phrasings plus the three cross-sentence tells; change
nothing else.

## Common mistakes

| Mistake | Fix |
|---|---|
| Adjectival passives survive ("the classpath is closed") | "the classpath stays closed" |
| Caveats "simplified" away | Keep every caveat; simplify wording only |
| Checker clean but prose fabricated facts | Re-diff facts against source bullets |
| Prose edited to satisfy a checker false positive | Fix the checker's whitelist instead |
