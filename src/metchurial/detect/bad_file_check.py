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
defense in the bad_files.tsv workflow (see cli.py) -- scan_file's own
try/except around the real work is the second, for whatever this cheap
check doesn't catch.

Deliberately NOT flagged here: a single token that happens to be one long
repeated character, e.g. a bare `3333333333333333` sitting in a real
predicate (`WHERE ACCT_NO = 3333333333333333`) -- a masked/dummy numeric
literal is completely normal, legitimate SQL data, unquoted DB2 NUMBER/
DECIMAL literals included, and unlike `========` a single token is exactly
one resync point for the tiered driver regardless of how repetitive its
characters are -- it's cheap to fail on, so there's no actual performance
problem here to defend against, only false-positive risk from guessing at
content that looks "decorative" to a human eye. See tests/test_bad_file_check.py's
TestSingleTokenValuesAreNotFlagged for the case this deliberately leaves alone.
"""

from __future__ import annotations

import re

from antlr4.Token import Token

from metchurial.models.bad_file import BadFileReason

# Above this fraction of *all lexical units encountered* (successfully
# lexed tokens, plus every character a lexer error swallowed) being lexer
# errors, the file is almost certainly not real SQL. The denominator is
# deliberately errors+tokens, not tokens alone: a lexer error consumes
# source text without emitting any token for it (see
# _longest_repeated_punct_run's docstring below), so dividing by token
# count alone lets the ratio run past 1.0 whenever errors outnumber
# tokens -- a file that's mostly bare non-ASCII prose with only a
# scattering of real SQL can print a nonsensical-looking "357% of tokens
# are lexer errors". errors/(errors+tokens) is a true fraction, bounded to
# [0, 1], so it always reads as an honest percentage. Deliberately high:
# legitimate SQL that just happens to use bare Korean column aliases
# extensively (a real, common pattern -- see README's Known Limitations on
# bare non-ASCII identifiers) lands well under this on its own without
# being remotely "bad". Only a much larger fraction reliably indicates
# prose/section-header text sitting directly in the file body rather than
# tightly interleaved with normal SQL tokens as an alias would be. 0.2
# here is the exact equivalent of the old tokens-only threshold (0.25) --
# same file, same verdict, just no longer a formula that can blow past
# 100%.
LEXER_ERROR_RATIO_THRESHOLD = 0.2

# A run of this many identical single-character punctuation tokens in a
# row is almost certainly a decorative divider line (`========`,
# `<<<<<<<<`) -- nothing in the grammar treats repeated punctuation as one
# unit, so each character becomes its own token the tiered driver must
# individually fail to make sense of.
MIN_PUNCTUATION_RUN = 6

# How much of the matched run/offending text to echo back in the reason
# string. Long enough to make '========' vs '--------' vs '........'
# visually obvious at a glance, short enough not to dump an entire
# divider line or a whole paragraph of unrecognized prose.
_PREVIEW_MAX_CHARS = 20

# The lexer's own error message is always exactly "token recognition
# error at: 'X'" for a single (possibly escaped, e.g. '\n') character --
# see antlr4.Lexer.notifyListeners/getErrorDisplay. Pulling the literal
# character back out of it, rather than just counting errors, is what
# lets the ratio-exceeded reason show *what* text it choked on.
_ERROR_CHAR_RE = re.compile(r"at: '(.*)'$")


def _preview(text: str) -> str:
    if len(text) > _PREVIEW_MAX_CHARS:
        return text[:_PREVIEW_MAX_CHARS] + "..."
    return text


def _longest_repeated_punct_run(all_tokens: list[Token]) -> tuple[int, str]:
    """Returns (run_length, source_text) for the longest run of identical
    single-character punctuation tokens that are contiguous *in the
    source*, not just adjacent in the token list.

    That distinction matters: a lexer error consumes source text without
    emitting any token for it, so bare non-ASCII prose sitting directly in
    the file body (e.g. Korean sentences, each word its own lexer error --
    see check_file_quality's ratio check just below) simply vanishes from
    `all_tokens`. Two sentence-ending periods that are actually paragraphs
    apart in the source end up back-to-back in the filtered token list,
    which used to make ordinary Korean prose look exactly like a
    decorative divider. Tracking each token's source offset and resetting
    the run whenever a gap opens up (i.e. some span of source text was
    swallowed by a lexer error rather than tokenized) fixes that without
    special-casing Korean or any other script -- a real divider like
    `========` or a spaced-out `- - - - -` has no such gap, since every
    character in it, punctuation or separating whitespace, is accounted
    for by a token.
    """
    best_len = 0
    best_range: tuple[int, int] | None = None
    run_len = 0
    run_start_idx = 0
    prev_type = None
    expected_pos = 0
    for i, t in enumerate(all_tokens):
        if t.type == Token.EOF:
            continue
        contiguous = t.start == expected_pos
        expected_pos = t.stop + 1
        if t.channel != Token.DEFAULT_CHANNEL:
            # Whitespace/comments don't break a spaced-out divider, but
            # only if nothing was swallowed just before them either.
            if not contiguous:
                run_len = 0
                prev_type = None
            continue
        is_punct = len(t.text) == 1 and not t.text.isalnum()
        if is_punct and contiguous and t.type == prev_type:
            run_len += 1
        elif is_punct:
            run_len = 1
            run_start_idx = i
            prev_type = t.type
        else:
            run_len = 0
            prev_type = None
        if is_punct and run_len > best_len:
            best_len = run_len
            best_range = (run_start_idx, i)

    if best_range is None:
        return 0, ""
    start_idx, end_idx = best_range
    snippet = "".join(tok.text for tok in all_tokens[start_idx:end_idx + 1])
    return best_len, snippet


def _error_item_preview(lexer_errors: list[tuple[int, int, str]]) -> str:
    """Reconstructs the actual offending text from lexer_errors' messages
    (each one names exactly the single character it choked on) so the
    ratio-exceeded reason can show *what* text tripped it instead of just
    a bare percentage."""
    chars = []
    for _line, _col, msg in lexer_errors:
        m = _ERROR_CHAR_RE.search(msg)
        if m:
            chars.append(m.group(1))
    return _preview("".join(chars))


def check_file_quality(all_tokens: list[Token],
                       lexer_errors: list[tuple[int, int, str]]) -> BadFileReason | None:
    """all_tokens/lexer_errors: statement_driver.lex_file()'s own return
    values -- this check is a byproduct of lexing, not a second pass.
    Returns None if the file looks like real SQL, or a BadFileReason
    (models/bad_file.py) if it looks "bad" enough to skip the expensive
    tiered parse for entirely."""
    total = sum(1 for t in all_tokens if t.type != Token.EOF)
    error_count = len(lexer_errors)
    if total == 0 and error_count == 0:
        # Nothing here at all (e.g. a genuinely empty file) -- nothing to
        # judge as bad. NOT the same as total == 0 with error_count > 0
        # (a file that's *entirely* unrecognized characters, not even
        # whitespace) -- that case falls through to the ratio check below,
        # which correctly reads as 100% rather than being silently waved
        # through just because there happen to be zero real tokens to
        # divide by.
        return None

    # errors+total, not total alone: a lexer error consumes source text
    # without emitting any token for it, so dividing by successfully-lexed
    # tokens alone isn't dividing by "the whole" -- see
    # LEXER_ERROR_RATIO_THRESHOLD's comment above for why that lets the
    # ratio run past 100%.
    ratio = error_count / (error_count + total)
    if ratio > LEXER_ERROR_RATIO_THRESHOLD:
        item = _error_item_preview(lexer_errors)
        return BadFileReason(
            category="lexer-error-ratio",
            item=item,
            message=("{:.0%} of all lexical content is lexer errors, e.g. '{}' (likely "
                     "non-SQL text, such as bare non-ASCII section headers, mixed "
                     "directly into the file body rather than inside a comment)"
                     ).format(ratio, item))

    run_len, run_text = _longest_repeated_punct_run(all_tokens)
    if run_len >= MIN_PUNCTUATION_RUN:
        item = _preview(run_text)
        return BadFileReason(
            category="repeated-char-run",
            item=item,
            message=("found a run of {} repeated punctuation characters in a row: '{}' "
                     "(likely a decorative divider line, not real SQL)"
                     ).format(run_len, item))

    return None
