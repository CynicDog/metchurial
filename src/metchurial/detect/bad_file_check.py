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

# How much of the matched run to echo back in the reason string. Long
# enough to make '========' vs '--------' vs '........' visually obvious
# at a glance, short enough not to dump an entire divider line.
_RUN_PREVIEW_MAX_CHARS = 20


def _longest_repeated_punct_run(all_tokens: list[Token]) -> tuple[int, str]:
    """Returns (run_length, source_text) for the longest run of identical
    single-character punctuation tokens that are contiguous *in the
    source*, not just adjacent in the token list.

    That distinction matters: a lexer error consumes source text without
    emitting any token for it, so bare non-ASCII prose sitting directly in
    the file body (e.g. Korean sentences, each word its own lexer error --
    see check_file_quality's ratio check just above) simply vanishes from
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


def _preview(text: str) -> str:
    if len(text) > _RUN_PREVIEW_MAX_CHARS:
        return text[:_RUN_PREVIEW_MAX_CHARS] + "..."
    return text


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

    run, run_text = _longest_repeated_punct_run(all_tokens)
    if run >= MIN_PUNCTUATION_RUN:
        return ("found a run of {} repeated punctuation characters in a row: '{}' "
               "(likely a decorative divider line, not real SQL)"
               ).format(run, _preview(run_text))

    return None
