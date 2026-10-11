#!/usr/bin/env bash
# Regression tests for scripts/check-docs-english.py.
#   tests/clean.md          plain prose: must stay 100% clean
#   tests/cliches.md        one cliché per sentence: every sentence flagged
#   tests/prose-baseline.md cliché-riddled guide: must fail at default threshold
#   tests/editorial.md      clichés + style violations under a "Why ..."
#                           heading: --cliches-only flags only the clichés
set -u
cd "$(dirname "$0")/.."
checker=scripts/check-docs-english.py
fail=0

out=$(python3 "$checker" tests/clean.md)
grep -q "clean (100%)" <<<"$out" || { echo "FAIL: clean.md not 100% clean"; echo "$out"; fail=1; }

out=$(python3 "$checker" tests/cliches.md)
grep -qE "TOTAL: 0/[0-9]+ clean" <<<"$out" || { echo "FAIL: cliches.md has unflagged sentences"; echo "$out"; fail=1; }

python3 "$checker" tests/prose-baseline.md >/dev/null 2>&1
[ $? -eq 1 ] || { echo "FAIL: prose-baseline.md did not fail the checker"; fail=1; }

# --cliches-only: flags clichés inside exempt sections, never style rules.
out=$(python3 "$checker" tests/editorial.md --cliches-only --examples 99); rc=$?
[ $rc -eq 1 ] || { echo "FAIL: editorial.md did not fail in --cliches-only mode"; fail=1; }
grep -q "it is important to note" <<<"$out" \
  || { echo "FAIL: --cliches-only missed a cliché in the exempt section"; fail=1; }
grep -qE "contraction \(|'may'/'might' \(use|progressive '-ing'|possible passive voice|sentence has|main statement" <<<"$out" \
  && { echo "FAIL: --cliches-only reported style rules"; echo "$out"; fail=1; }

out=$(python3 "$checker" tests/clean.md --cliches-only)
grep -q "clean (100%)" <<<"$out" || { echo "FAIL: clean.md not clean in --cliches-only mode"; fail=1; }

# Default mode keeps exempting "Why ..." sections.
out=$(python3 "$checker" tests/editorial.md)
grep -qE "TOTAL: 0/1 clean" <<<"$out" \
  || { echo "FAIL: default mode lost the editorial exemption"; fail=1; }

[ $fail -eq 0 ] && echo "all tests passed"
exit $fail
