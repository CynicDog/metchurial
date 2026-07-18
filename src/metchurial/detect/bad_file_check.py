# -*- coding: utf-8 -*-
"""Cheap, lex-only pre-check for whether a file is likely not real SQL at
all -- decorative divider lines (`========`, `<<section>>`), or prose/
section headers (often in bare, unquoted non-ASCII text) sitting directly
in the file body rather than inside a real `--`/`/* */` comment.

Both patterns make the tiered parse driver's per-token error-recovery cost
balloon (every token becomes its own resync/mismatch point -- see
statement_driver.py's module docstring) without producing any meaningful
result anyway, so it's cheaper and more honest to flag the file up front
than to spend minutes grinding through it. This is the first line of
defense in the bad_files.txt workflow (see cli.py) -- scan_file's own
try/except around the real work is the second, for whatever this cheap
check doesn't catch.
"""

from __future__ import annotations

from antlr4.Token import Token

# Above this fraction of (non-EOF) tokens being lexer errors, the file is
# almost certainly not real SQL. Deliberately high: legitimate SQL that
# just happens to use bare Korean column aliases extensively (a real,
# common pattern -- see README's Known Limitations on bare non-ASCII
# identifiers) lands in the 5-10% range on its own without being remotely
# "bad". Only a much larger fraction reliably indicates prose/section-
# header text sitting directly in the file body rather than tightly
# interleaved with normal SQL tokens as an alias would be.
LEXER_ERROR_RATIO_THRESHOLD = 0.25

# A run of this many identical single-character punctuation tokens in a
# row is almost certainly a decorative divider line (`========`,
# `<<<<<<<<`) -- nothing in the grammar treats repeated punctuation as one
# unit, so each character becomes its own token the tiered driver must
# individually fail to make sense of.
MIN_PUNCTUATION_RUN = 6


def _longest_repeated_punct_run(tokens: list[Token]) -> int:
    best = 0
    current = 0
    prev_type = None
    for t in tokens:
        if t.channel != Token.DEFAULT_CHANNEL:
            continue
        if len(t.text) == 1 and not t.text.isalnum() and t.type == prev_type:
            current += 1
        else:
            current = 1
            prev_type = t.type
        best = max(best, current)
    return best


def check_file_quality(all_tokens: list[Token],
                       lexer_errors: list[tuple[int, int, str]]) -> str | None:
    """all_tokens/lexer_errors: statement_driver.lex_file()'s own return
    values -- this check is a byproduct of lexing, not a second pass.
    Returns None if the file looks like real SQL, or a short human-
    readable reason string if it looks "bad" enough to skip the expensive
    tiered parse for entirely."""
    total = sum(1 for t in all_tokens if t.type != Token.EOF)
    if total == 0:
        return None

    ratio = len(lexer_errors) / total
    if ratio > LEXER_ERROR_RATIO_THRESHOLD:
        return ("{:.0%} of tokens are lexer errors (likely non-SQL text, e.g. bare "
               "non-ASCII section headers, mixed directly into the file body rather "
               "than inside a comment)").format(ratio)

    run = _longest_repeated_punct_run(all_tokens)
    if run >= MIN_PUNCTUATION_RUN:
        return ("found a run of {} repeated punctuation characters in a row "
               "(likely a decorative divider line such as '========', not real SQL)"
               ).format(run)

    return None
