#!/usr/bin/env python3
"""Check ASD-STE100 style for the prose in docs/.

This applies the measurable core of ASD-STE100 (Simplified Technical
English):

- Sentence length: at most 25 words in the main statement, 30 words total.
- No "may" or "might".
- No progressive "-ing" verb forms.
- No passive voice (heuristic: form of "be" + past participle).
- No "etc.", "e.g.", "i.e.", "&", "let's", or contractions.

It checks paragraphs and list items. It skips headings, tables, code
blocks, inline code, and link targets. docs/index.md and "Why ..."
editorial sections are exempt (see AGENTS.md).

Exit status is 0 when the corpus-wide clean-sentence rate is at least
--threshold.

Usage:
  python3 scripts/check-docs-english.py [path ...] [--threshold 0.80]

With no path arguments it checks every Markdown file under ./docs of the
current directory. Point it at any file or directory you pass explicitly.
"""

import argparse
import re
import sys
from pathlib import Path

DOCS = Path.cwd() / "docs"
EXEMPT_FILES = {(DOCS / "index.md").resolve()}

HEADING = re.compile(r"^(#{1,6})\s+(.*)$")
EXEMPT_HEADING = re.compile(r"^\s*[Ww]hy\b")
BULLET = re.compile(r"^\s*(?:[-*+]|\d+[.)])\s+")
ITEM = re.compile(r"^\s*(?:[-*+]|\d+[.)])\s+\S")
TABLE = re.compile(r"^\s*\|")
FENCE = re.compile(r"^(```|~~~)")
SENTENCE_END = re.compile(r"(?<=[.!?])\s+")

IMG_LINK = re.compile(r"!\[([^\]]*)\]\([^)]*\)")
LINK = re.compile(r"\[([^\]]*)\]\([^)]*\)")
INLINE_CODE = re.compile(r"`[^`\n]*`")
MARKUP = re.compile(r"\*{1,3}|_{1,3}")

AUX = r"(?:am|is|are|was|were|be|been|being)"
# "-ing" words that follow "be" but are not progressive verbs.
ING_NOUNS = r"(?!(?:no|some|any|every)thing\b|missing\b|during\b)"
# "-ed"/"-en" words that follow "be" but are not past participles.
PARTICPLE_FALSE_POSITIVES = r"(?!often\b|speed\b|need\b|seed\b|feed\b|open\b|then\b|when\b)"
PROGRESSIVE = re.compile(rf"\b{AUX}\s+{ING_NOUNS}\w*ing\b", re.I)
PASSIVE = re.compile(rf"\b{AUX}\s+(?:\w+ly\s+)?{PARTICPLE_FALSE_POSITIVES}\w*(?:ed|en)\b", re.I)
MODAL = re.compile(r"\b(?:may|might)\b", re.I)
CONTRACTION = re.compile(
    r"\b\w+n['\u2019]t\b"
    r"|\b\w+['\u2019](?:re|ve|ll|d|m)\b"
    r"|\b(?:it|there|that|what|who|he|she|where|how|when|why|this|one)['\u2019]s\b",
    re.I,
)
BANNED = [
    (re.compile(r"\betc\.?\b", re.I), "'etc.' (list all the items)"),
    (re.compile(r"\be\.g\.", re.I), "'e.g.' (give one example with 'for example')"),
    (re.compile(r"\bi\.e\.", re.I), "'i.e.' (say 'that is')"),
    (re.compile(r"&amp;|&"), "'&' (say 'and')"),
    (re.compile(r"\blet's\b", re.I), "'let's' (use the imperative mood)"),
    (CONTRACTION, "contraction (write the full words)"),
]

MAX_SENTENCE = 30
MAX_MAIN_STATEMENT = 25


def prose_blocks(text):
    """Yield (line_number, block_text) for each prose block in the file."""
    lines = text.splitlines()
    if lines and lines[0].strip() == "---":
        rest = lines[1:]
        rest = rest[rest.index("---") + 1:]
        lines = rest

    buf, buf_line = [], None
    fence = None
    exempt_level = None

    def flush():
        nonlocal buf, buf_line
        if buf:
            yield_line, yield_text = buf_line, " ".join(buf)
            buf, buf_line = [], None
            return yield_line, yield_text
        return None

    for i, raw in enumerate(lines, 1):
        stripped = raw.strip()
        fence_match = FENCE.match(stripped)
        if fence_match:
            done = flush()
            if done:
                yield done
            if fence is None:
                fence = fence_match.group(1)
            elif stripped.startswith(fence):
                fence = None
            continue
        if fence is not None:
            continue

        heading = HEADING.match(raw)
        if heading:
            done = flush()
            if done:
                yield done
            level = len(heading.group(1))
            if exempt_level and level <= exempt_level:
                exempt_level = None
            if EXEMPT_HEADING.match(heading.group(2)):
                exempt_level = level
            continue
        if exempt_level:
            continue

        if not stripped or TABLE.match(raw):
            done = flush()
            if done:
                yield done
            continue

        if ITEM.match(raw):
            # Each list item is its own block: continuation lines join the
            # item, a new item starts a new block.
            done = flush()
            if done:
                yield done

        text_line = stripped.lstrip(">").strip() if stripped.startswith(">") else stripped
        text_line = BULLET.sub("", text_line)
        if buf_line is None:
            buf_line = i
        buf.append(text_line)

    done = flush()
    if done:
        yield done


def clean(text):
    text = IMG_LINK.sub(r"\1", text)
    text = LINK.sub(r"\1", text)
    text = INLINE_CODE.sub(" ", text)
    text = MARKUP.sub("", text)
    return text


def check_sentence(sentence):
    """Return a list of problems with the sentence (empty if compliant)."""
    words = sentence.split()
    problems = []
    if len(words) > MAX_SENTENCE:
        problems.append(f"sentence has {len(words)} words (max {MAX_SENTENCE})")
    else:
        head, comma, _ = sentence.partition(",")
        if comma and len(head.split()) > MAX_MAIN_STATEMENT:
            problems.append("main statement over 25 words")
    if MODAL.search(sentence):
        problems.append("'may'/'might' (use 'can', 'must', or the imperative)")
    if PROGRESSIVE.search(sentence):
        problems.append("progressive '-ing' verb form")
    if PASSIVE.search(sentence):
        problems.append("possible passive voice")
    for pattern, label in BANNED:
        if pattern.search(sentence):
            problems.append(label)
    return problems


def check_file(path):
    """Return (total, clean, violations) for one Markdown file."""
    total = clean_count = 0
    violations = []
    for line_no, block in prose_blocks(path.read_text()):
        for sentence in SENTENCE_END.split(clean(block)):
            sentence = sentence.strip()
            if len(sentence.split()) < 2:
                continue
            total += 1
            problems = check_sentence(sentence)
            if problems:
                excerpt = sentence if len(sentence) <= 90 else sentence[:87] + "..."
                violations.append((line_no, problems, excerpt))
            else:
                clean_count += 1
    return total, clean_count, violations


def main():
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("paths", nargs="*", help="Markdown files to check (default: docs/)")
    parser.add_argument("--threshold", type=float, default=0.80,
                        help="minimum corpus-wide clean-sentence rate (default: 0.80)")
    parser.add_argument("--examples", type=int, default=0,
                        help="show at most N violations per file")
    args = parser.parse_args()

    if args.paths:
        files = []
        for p in args.paths:
            p = Path(p).resolve()
            files.extend(sorted(p.rglob("*.md")) if p.is_dir() else [p])
        files = sorted(set(files))
    else:
        files = sorted(DOCS.rglob("*.md"))

    grand_total = grand_clean = 0
    failures = False
    for path in files:
        try:
            rel = path.relative_to(Path.cwd())
        except ValueError:
            rel = path
        if path.resolve() in EXEMPT_FILES:
            print(f"{rel}: exempt")
            continue
        total, clean_count, violations = check_file(path)
        if total == 0:
            continue
        pct = 100 * clean_count / total
        grand_total += total
        grand_clean += clean_count
        flag = "" if clean_count / total >= args.threshold else "  BELOW"
        print(f"{rel}: {clean_count}/{total} clean ({pct:.0f}%){flag}")
        if args.examples:
            for line_no, problems, excerpt in violations[:args.examples]:
                print(f"  line {line_no}: {', '.join(problems)}: {excerpt!r}")
        if violations and clean_count / total < args.threshold:
            failures = True

    if grand_total == 0:
        print("no prose sentences found")
        return 0
    rate = grand_clean / grand_total
    verdict = "PASS" if rate >= args.threshold and not failures else "FAIL"
    print(f"TOTAL: {grand_clean}/{grand_total} clean ({rate:.0%}, threshold {args.threshold:.0%}) {verdict}")
    return 0 if verdict == "PASS" else 1


if __name__ == "__main__":
    sys.exit(main())
