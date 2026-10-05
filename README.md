# Docs Writing

Docs Writing is an agent skill for technical documentation. It writes
and reviews prose in simplified technical English, following the
ASD-STE100 standard. It automates the checkable rules and keeps the
facts intact while it rewrites.

The repo has two parts:

- `SKILL.md` — the rules the agent follows
- `scripts/check-docs-english.py` — the checker, a Python 3 script with
  no dependencies

## Prose rules

The skill applies a small set of rules:

- One idea per sentence. At most 25 words in the main statement, 30 total.
- Active voice, simple present. Imperative mood for steps.
- `can` for ability, `must` for obligation. No `may` or `might`.
- No idioms, metaphors, contractions, `etc.`, `e.g.`, `i.e.`, or `&`.
- One term, one meaning.

A before/after example:

```
Freshly published versions are refused by a cooldown window
until they have had time to be noticed.
```

```
A cooldown window rejects new versions. The delay gives you
time to notice a problem.
```

## Checker

Run the checker from the repo root:

```
python3 scripts/check-docs-english.py docs/
```

Pass any file or directory instead. Without a path, the checker tests
every Markdown file under `docs/` of the current directory.

It checks each sentence in a paragraph or list item:

- Length: 25 words or fewer in the main statement, 30 total
- Modals: no `may` or `might`
- Progressive forms (`is building`)
- Passive voice (a heuristic)
- Banned words: `etc.`, `e.g.`, `i.e.`, `&`, `let's`, contractions

It skips headings, tables, code blocks, inline code, and link targets.
It exempts `docs/index.md` and sections under a "Why ..." heading.

The output shows a clean-sentence rate for each file and for all files
together. The checker exits non-zero when any rate is below the
threshold, which defaults to 0.80.

```
python3 scripts/check-docs-english.py docs/ --threshold 0.9
python3 scripts/check-docs-english.py docs/ --examples 5
```

`--examples N` prints the first N violations of each file.

## Install

Clone the repo into your agent's skills directory:

```
git clone https://github.com/brutasse/docs-writing ~/.agents/skills/docs-writing
```

If your agent uses another path, clone there instead.

## License

The license for this repo is MIT. See `LICENSE`.
