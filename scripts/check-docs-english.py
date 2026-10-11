#!/usr/bin/env python3
"""Check ASD-STE100 style for the prose in docs/.

This applies the measurable core of ASD-STE100 (Simplified Technical
English):

- Sentence length: at most 25 words in the main statement, 30 words total.
- No "may" or "might".
- No progressive "-ing" verb forms.
- No passive voice (heuristic: form of "be" + past participle).
- No "etc.", "e.g.", "i.e.", "&", "let's", or contractions.
- No LLM clichés (ported from Simon Willison's cliché highlighter; see
  SKILL.md).

It checks paragraphs and list items. It skips headings, tables, code
blocks, inline code, and link targets. docs/index.md and "Why ..."
editorial sections are exempt (see AGENTS.md).

Exit status is 0 when the corpus-wide clean-sentence rate is at least
--threshold.

Usage:
  python3 scripts/check-docs-english.py [path ...] [--threshold 0.80]

With no path arguments it checks every Markdown file under ./docs of the
current directory. Point it at any file or directory you pass explicitly.
With --cliches-only, check only for LLM clichés: the style rules above
don't apply and exempt files and sections are checked anyway (see
SKILL.md "Where the rules bend").
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

# --- LLM clichés ------------------------------------------------------------
# Ported from Simon Willison's cliché highlighter
# (https://tools.simonwillison.net/llm-cliche-highlighter), which inventories
# rhetorical tells plus Wikipedia's "Signs of AI writing". Tuned for a docs
# corpus: "the entire/whole X" only flags rhetorical nouns ("whole number" is
# math); "X is dead" only flags a clause-final "dead" ("the connection is dead
# when ..." is literal); "underscore" only flags the verb, never the character
# name; "Do not call it X. Call it Y." only flags call/name, since imperative
# "do not X it. X it." is normal in guidance. Colon-into-a-triple is dropped:
# in reference prose it is usually a real enumeration. Tells that span
# sentences (echoed skeletons, stacked questions, repeated sentence openers)
# are SKILL.md rules, not checker rules.

# Chain "HEAD item, HEAD item, ..." separators and item bodies.
CH_BODY = r"[^,.;:!?\n–—…]*"
CH_SEP = r"(?:\s*,\s*(?:and\s+|or\s+)?|\s+(?:and|or)\s+|\s*[;&–—]\s*(?:and\s+|or\s+)?|\s+-{1,2}\s+)"
# Nouns that mark the "is the entire/whole X" rhetorical flourish.
RHET = r"(?:point|game|thing|trick|pitch|idea|secret|answer|argument|claim|product|problem|premise|plan|promise|appeal|charm|value|goal|purpose|story)"
APOS = "['’]"

CLICHES = [
    (re.compile(r"\bno[-\s]" + CH_BODY + r"(?:" + CH_SEP + r"no[-\s]" + CH_BODY + r")+", re.I),
     "'no X, no Y' chain (state each fact in a plain sentence)"),
    (re.compile(r"\b(?:that|this)\s+(?:is|was)\s+the\s+whole\s+" + RHET +
                r"|\b(?:is|was|are|were)\s+the\s+(?:whole|entire)\s+" + RHET +
                r"|\bhere\s+is\s+the\s+whole\s+" + RHET +
                r"|\bthe\s+entire\s+" + RHET + r"\b[^.!?\n]{0,40}?\b(?:is|was|are|were)\b", re.I),
     "'is the whole/entire point' flourish (state the point plainly)"),
    (re.compile(r"\b(?:did\s+not|didn" + APOS + r"t)\s" + CH_BODY +
                r"(?:" + CH_SEP + r"(?:did\s+not|didn" + APOS + r"t)\s" + CH_BODY + r")+", re.I),
     "'did not X, did not Y' chain (state each fact in a plain sentence)"),
    (re.compile(r"\bsit(?:s|ting)?\s+with\s+(?:that|this|it|(?:the|your)\s+"
                r"(?:discomfort|feelings?|tension|weight|uncertainty|ambiguity|grief|silence|unease))\b", re.I),
     "'sit with that' (delete the cue to reflect)"),
    (re.compile(r"\byou\s+already\s+knows?\s+(?:the\s+answer|what|how|why|this|that|it|who|where)\b"
                r"|\byou\s+already\s+knows?\b(?![ \t]+\w)", re.I),
     "'you already know' (assert the fact instead)"),
    (re.compile(r"\bis\s+(?:(?:the|a)\s+real\b(?![\s-]+(?:estate|time|life|world|quick|number)\b)[^.!?\n]*?\b(?:and|not)\s+it\b"
                r"|real\b(?![\s-]+(?:estate|time|life|world|quick|number)\b)[^.!?\n]*?\b(?:and|not)\b)", re.I),
     "'the X is real, and/not ...' (assert the fact without the staging)"),
    (re.compile(r"\bthe\s+punchline(?:\s+(?:is|was|being)\b|\s*[:?])", re.I),
     "'the punchline is' (state the conclusion directly)"),
    (re.compile(r"(?:\b(?:is|are|was|were|feels?|felt|seems?|seemed)\b|['’]s)\s+(?:\w+\s+){0,2}?worth\s+naming\b(?!\s+names\b)"
                r"|\bworth\s+naming\s*:", re.I),
     "'worth naming' (state the fact without the framing)"),
    (re.compile(r"\b(?:that|this|it|which)(?:['’]s|\s+(?:is|was))\s+not\s+nothing\b", re.I),
     "'that is not nothing' (state the size or effect)"),
    (re.compile(r"^I\s+(?:will\s+not|won" + APOS + r"t)\s+pretend\b"
                r"|I" + APOS + r"ll\s+be\s+(?:honest|clear|blunt|real)\b"
                r"|let(?:\s+us|s|['’]s)\s+be\s+(?:honest|clear|blunt|real)\b"
                r"|to\s+be\s+(?:honest|clear|blunt|real)\b"
                r"|^(?:Honestly|Look|Truthfully|Frankly)\s*,", re.I),
     "announced sincerity ('to be honest', 'I will not pretend', 'Honestly,')"),
    (re.compile(r"\b(?:that|this|it)(?:['’]s|\s+(?:is|was))\s+the\s+part\b"
                r"|\bthe\s+part\s+that\s+(?:makes|made|gets|got|keeps|kept)\s+(?:me|you|us|it)\b"
                r"|\bmy\s+favou?rite\s+part\s+of\b", re.I),
     "'that is the part ...' (state the detail instead of gesturing at it)"),
    (re.compile(r"\bthe\s+only\s+[\w'’-]+(?:\s+[\w'’-]+){0,2}?\s+(?:I|you|we|it|he|she|they)\s+"
                r"(?:trust|need|needs|care|cares|want|wants|use|uses|believe|believes)\b"
                r"|\bthe\s+only\s+[\w'’-]+\s+that\s+(?:matters|counts|works|survives)\b", re.I),
     "'the only X I trust' (give the judgment plainly)"),
    (re.compile(r"\b(?:you\s+)?(?:do\s+not|don" + APOS + r"t)\s+(?:have\s+to\s+)?take\s+my\s+word\s+for\s+"
                r"(?:it|any\s+of\s+(?:it|this|that))\b", re.I),
     "'do not take my word for it' (cite the source or delete)"),
    (re.compile(r"^Turns\s+out\b|\bit\s+turns\s+out\s+that\b", re.I),
     "'(it) turns out' (state the finding directly)"),
    (re.compile(r"\b(?:hold|fit|fits|holds|held)\s+(?:it\s+)?in\s+your\s+head\b"
                r"|\bbatteries[-\s]included\b|\bit\s+just\s+works\b"
                r"|\bzero[-\s]config(?:uration)?\b|\bsane\s+defaults\b", re.I),
     "simplicity boilerplate ('fits in your head', 'sane defaults', 'it just works')"),
    (re.compile(r"\bhere(?:['’]s|\s+is)\s+(?:the|a|my|one)\s+"
                r"(?:twist|thing|catch|kicker|rub|problem|first|second|third|next|recent|real|best|worst|surprising|interesting|key|important)\b[\w\s-]{0,20}[:.]", re.I),
     "'here is the thing:' (delete the cue, start with the fact)"),
    (re.compile(r"\b[\w'’\s-]{2,30}\s(?:is|are)\s+dead\s*[.!?;,:]", re.I),
     "'X is dead' obituary (say what replaces it or that it is unsupported)"),
    (re.compile(r"\blong\s+live\b", re.I),
     "'long live X' obituary sequel (state the replacement)"),
    (re.compile(r"\b(?:that|this)(?:['’]s|\s+(?:is|was))\s+why\b[^.!?\n]{0,80}?\b(?:matter(?:s|ed)?|count(?:s|ed)?)\b", re.I),
     "'that is why X mattered' (explain the significance in one sentence)"),
    (re.compile(r"[;:,]\s+[^.;:!?\n]{2,50}\s(?:did|does|do|was|were|is|are|has|have|had|can|could|would|will)(?:\s+not|n" + APOS + r"t)?[.;]"
                r"|\b(?:Maybe|Perhaps)\s+\w+[^.!?\n]{0,40}\s(?:would|could|might|should|did|had|was|is)(?:\s+not|n" + APOS + r"t)?\s+(?:have\s*)?\.", re.I),
     "stranded-auxiliary reversal ('the data did not.') (finish the contrast in full words)"),
    (re.compile(r"\b(?:delv(?:e|es|ed|ing)|tapestr(?:y|ies)|meticulous(?:ly)?|pivotal|intricate(?:ly)?"
                r"|intricacies|interplay|underscor(?:es|ed|ing)\s+(?:the|that|this|these|those|how|what|why|their|its|our|your|a|an)|garner(?:s|ed|ing)?|bolster(?:s|ed|ing)?"
                r"|vibrant|bustling|multifaceted|seamless(?:ly)?|commendable|ever-evolving)\b", re.I),
     "AI vocabulary ('delve', 'seamless', 'pivotal', 'underscores') (use plain words)"),
    (re.compile(r"\bnot\s+(?:just|only|merely|simply)\s+[^.!?\n;]*?\bbut(?:\s+also)?\b"
                r"|\b(?:it|this|that)(?:['’]s|\s+(?:is|was))\s+not\s+[^.!?\n,;—–]{1,60}[,;—–]\s*"
                r"(?:it|this|that)(?:['’]s|\s+(?:is|was))\b", re.I),
     "'not just X, but Y' (state Y directly)"),
    (re.compile(r"\bnot\s+(?!(?:just|only|merely|simply)\b)[^.!?\n;]{1,100}?[,:;]\s*but\b", re.I),
     "'not X, but Y' (state what is true)"),
    (re.compile(r"\bit(?:['’]s|\s+(?:is|was))\s+(?:also\s+)?(?:important|worth|crucial|essential|vital)\s+"
                r"(?:to\s+(?:note|remember|understand|recogni[sz]e|mention|pause|consider|ask)"
                r"|noting|mentioning|remembering|pausing|considering|asking)\b(?:\s+that\b)?"
                r"|\bit\s+should\s+be\s+noted\b", re.I),
     "'it is important to note' (state the fact)"),
    (re.compile(r"\b(?:stand|stands|stood|serve|serves|served|standing|serving)\s+as\s+(?:a|an)\s+"
                r"(?:\w+\s+)?(?:testament|reminder)\b"
                r"|\b(?:is|was|are|were|remain|remains)\s+a\s+(?:\w+\s+)?testament\s+to\b", re.I),
     "'stands as a testament' (say what happened)"),
    (re.compile(r"\bplay(?:s|ed|ing)?\s+(?:a|an)\s+(?:\w+\s+)?(?:crucial|pivotal|vital|key|significant|central|critical|important)\s+role\b", re.I),
     "'plays a crucial role' (say what it does)"),
    (re.compile(r"\b(?:ever-)?(?:evolving|changing|shifting)\s+landscape\b"
                r"|\bin\s+today" + APOS + r"s\s+(?:fast-paced|ever-changing|ever-evolving|digital|modern|competitive)\s+\w+", re.I),
     "scene-setting boilerplate ('ever-evolving landscape', 'in today's world')"),
    (re.compile(r"\b(?:many|some|several|most|numerous)?\s*(?:experts|critics|observers|scholars|analysts|commentators)\s+"
                r"(?:have\s+|often\s+|widely\s+)?(?:argu(?:e|es|ed)|not(?:e|es|ed)|suggest(?:s|ed)?"
                r"|believ(?:e|es|ed)|agree[ds]?|contend(?:s|ed)?|observ(?:e|es|ed)|caution(?:s|ed)?"
                r"|claim(?:s|ed)?|cit(?:e|es|ed)|point(?:s|ed)?\s+out)\b"
                r"|\bindustry\s+reports?\s+(?:suggest|indicate|show)\w*\b", re.I),
     "vague attribution ('experts argue') (name the source or delete)"),
    (re.compile(r"\bdespite\s+(?:these|those|such|its|their|the|numerous|significant|ongoing)\s+(?:\w+\s+)?challenges\b"
                r"|\bfac(?:e|es|ed|ing)\s+(?:several|numerous|many|significant|various|a\s+number\s+of)\s+challenges\b"
                r"|\bchallenges\s+remain\b|\bremains\s+to\s+be\s+seen\b|\b(?:only\s+)?time\s+will\s+tell\b", re.I),
     "challenges/outlook boilerplate ('despite these challenges', 'time will tell')"),
    (re.compile(r",\s+(?:highlighting|underscoring|emphasizing|showcasing|reflecting|demonstrating"
                r"|illustrating|signaling|solidifying|cementing|reinforcing|underlining)\s+"
                r"(?:its|his|her|their|our|the|a|an|how|that|what|both)\b[^.!?\n]*", re.I),
     "', highlighting the ...' tail (drop the tail; make a plain sentence if needed)"),
    (re.compile(r"\bnestled\s+(?:in|on|among|between|along|at)\b|\bin\s+the\s+heart\s+of\b"
                r"|\brich\s+(?:cultural\s+|historical\s+)?(?:heritage|history|tapestry)\b|\bhidden\s+gem\b"
                r"|\bmust-(?:visit|see|try)\b|\bbreathtaking\b|\bboasts?\s+(?:a|an|the)\b"
                r"|\bstunning\s+(?:views?|scenery|architecture|backdrop)\b", re.I),
     "promotional tone ('boasts a', 'hidden gem', 'in the heart of') (write neutral description)"),
    (re.compile(r"\bas\s+an\s+ai(?:\s+language)?\s+model\b|\bas\s+of\s+my\s+last\s+(?:update|training)\b"
                r"|\bknowledge\s+cutoff\b"
                r"|\bI\s+(?:cannot|can" + APOS + r"t|do\s+not|don" + APOS + r"t)\s+(?:browse\s+the\s+internet|access\s+real-?time)\b"
                r"|contentReference|oaicite|turn0(?:search|news|image)\d*|attributableIndex|utm_source=", re.I),
     "chatbot leftover ('as of my last update', 'knowledge cutoff') (delete)"),
]

# Cliché shapes that span two sentences inside one block.
CLICHES_BLOCK = [
    (re.compile(r"\b(?:do\s+not|don" + APOS + r"t)\s+(?:just\s+|simply\s+)?(call|name)\b[^.!?]*?[.!?]\s*"
                r"(?:just\s+|simply\s+)?\1\b", re.I),
     "'Do not call it X. Call it Y.' reversal (use the term directly)"),
    (re.compile(r"\b(?:isn" + APOS + r"t|is\s+not)\s+[^.!?]{1,80}[.!?]\s*"
                r"(?:it" + APOS + r"s|it\s+is|this" + APOS + r"s|this\s+is|that" + APOS + r"s|that\s+is)\b", re.I),
     "'isn't X. It's Y.' reversal (state what it is)"),
]

MAX_SENTENCE = 30
MAX_MAIN_STATEMENT = 25


def prose_blocks(text, cliches_only=False):
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
            if not cliches_only and EXEMPT_HEADING.match(heading.group(2)):
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


def check_sentence(sentence, cliches_only=False):
    """Return a list of problems with the sentence (empty if compliant)."""
    problems = []
    if not cliches_only:
        words = sentence.split()
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
    for pattern, label in CLICHES:
        if pattern.search(sentence):
            problems.append(label)
    return problems


def check_file(path, cliches_only=False):
    """Return (total, clean, violations) for one Markdown file."""
    total = clean_count = 0
    violations = []
    for line_no, block in prose_blocks(path.read_text(), cliches_only):
        block_problems = [label for pattern, label in CLICHES_BLOCK
                          if pattern.search(clean(block))]
        for sentence in SENTENCE_END.split(clean(block)):
            sentence = sentence.strip()
            if len(sentence.split()) < 2:
                continue
            total += 1
            problems = check_sentence(sentence, cliches_only)
            problems += [p for p in block_problems if p not in problems]
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
    parser.add_argument("--cliches-only", action="store_true",
                        help="flag only LLM clichés; skip style rules and exemptions")
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
        if not args.cliches_only and path.resolve() in EXEMPT_FILES:
            print(f"{rel}: exempt")
            continue
        total, clean_count, violations = check_file(path, args.cliches_only)
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
