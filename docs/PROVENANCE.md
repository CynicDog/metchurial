# Third-party provenance

metchurial's own code is MIT-licensed (see the repository-root `LICENSE`
file); everything below concerns the third-party code it vendors.

This project vendors two pieces of third-party, permissively-licensed code
so that the final deployable artifact (`dist/metchurial.py`)
can run with zero `pip install`s in a restricted target environment. Both
are reproduced here for the company's third-party-code intake process to
review before `dist/metchurial.py` is carried into the
restricted environment.

## 1. Db2 SQL grammar (`vendor/grammars-v4/`)

- **Source**: [`antlr/grammars-v4`](https://github.com/antlr/grammars-v4),
  path `sql/db2/`.
- **Commit vendored**: `7d16f6dd457301340d0ae11e7d9d03269f682afd` (2026-07-12).
- **Files vendored**: `Db2Lexer.g4`, `Db2Parser.g4`.
- **License**: MIT. `grammars-v4` has no single repo-wide license
  (confirmed: GitHub's license-detection API returns 404 for this repo —
  each grammar carries its own license in a file header); the MIT header
  embedded at the top of `Db2Lexer.g4`/`Db2Parser.g4` is the operative grant:

  ```
  IBM Db2 SQL grammar.
  The MIT License (MIT).

  Copyright (c) 2023, Michał Lorek.
  ```

  The full MIT license text is vendored alongside at
  `vendor/grammars-v4/LICENSE-mit.txt`, per the MIT license's requirement
  to include a copy of the license with any redistribution.
- **Modifications**: `Db2Parser.g4`'s `fetch_clause` rule was changed from

  ```
  fetch_clause
      : FETCH NEXT fetch_row_count? row_rows ONLY
      ;
  ```

  to

  ```
  fetch_clause
      : FETCH (NEXT | FIRST) fetch_row_count? row_rows ONLY
      ;
  ```

  to add the also-valid, commonly-used `FETCH FIRST ... ROWS ONLY` form
  (the grammar previously modeled only `FETCH NEXT`). Both `NEXT` and
  `FIRST` already existed as lexer tokens, so this was a one-line grammar
  change, not a new token. This is called out
  here per the file actually having changed, not as a formality --
  `tests/test_grammar_smoke.py`'s `TestFetchRowLimiting` pins down both
  forms parsing identically.

  A second, larger round of modifications (issue #4, commit `7fea4c8`)
  fixed three real parse-path gaps rather than adding a variant form:

  1. `table_reference` gained ANSI `JOIN ... ON`/`USING` and `CROSS JOIN`
     alternatives, merged in as *direct* left recursion (ANTLR4 rejects
     the original `joined_table` rule's shape as mutually left-recursive
     with `table_reference`, which is almost certainly why its only
     reference site had been commented out rather than fixed). The
     now-redundant standalone `joined_table` rule was removed.
  2. `common_table_expression`'s body, previously self-referential
     (`(WITH common_table_expression)? ')'`, no way for a CTE's own SELECT
     to ever enter the tree), now points at
     `(WITH common_table_expression_list)? fullselect`, the same shape
     already used by `select_statement` and every other CTE-consuming rule
     in this grammar.
  3. `function_invocation`'s `arg_list` became optional
     (`arg_list?` instead of `arg_list`), so zero-argument calls like
     `NOW()` now have a parse path.

  All three were previously tracked as accepted, worked-around limitations
  (issues #1/#2); see CynicDog/metchurial#4 for the full investigation and
  antlr/grammars-v4#4936 for the upstream PR against the source grammar.
  `tests/test_grammar_fix_regression.py` pins all three down end-to-end
  through the actual scan pipeline, not just at the grammar-rule level.

  A third round of modifications fixed three more parse-path gaps found
  while hardening SQL query identification:

  1. `function_name` gained explicit alternatives for common DB2 built-in
     names that are reserved lexer tokens rather than plain `ID`
     (`COUNT`, `MAX`, `LOWER`, `CONCAT`, `LENGTH`, `VALUE`, `CHAR`,
     `DATE`, `TIME`, `TIMESTAMP`, `DECIMAL`, `INT`, `INTEGER`,
     `REPLACE`), so `SELECT COUNT(x) ...` parses as one clean tree
     instead of shredding into resync fragments. Reserved names with an
     expression-position role of their own (`EXISTS`, `CAST`,
     `YEAR`/`MONTH`/... labeled durations) were deliberately excluded to
     avoid ambiguity.
  2. `having_clause` was `: search_condition ;` with no `HAVING` keyword
     at all -- and no `HAVING` token existed in `Db2Lexer.g4` (the only
     lexer modification to date adds it). Any statement with a HAVING
     clause previously failed to parse past its GROUP BY.
  3. `order_by_clause` was missing its leading `ORDER BY` tokens (compare
     `window_order_clause`, which has them), so `GROUP BY ... ORDER BY`
     failed with `mismatched input 'BY' expecting 'OF'`.

  `tests/test_query_identity_complex.py` pins these end-to-end through
  the scan pipeline.
- **Why this grammar over the previously-used Oracle PL/SQL grammar**:
  this project originally used `sql/plsql` (Oracle's grammar) as a
  stand-in, on the mistaken belief that no maintained DB2 grammar existed
  in `grammars-v4` -- a real research gap (an earlier web search didn't
  surface `sql/db2`; it exists and is purpose-built for "IBM Db2 LUW").
  Switching removed the structural-mismatch risk of borrowing a different
  vendor's SQL dialect: DB2-specific constructs (host variables,
  `expression`/`predicate` shapes) are now modeled directly rather than
  approximated via Oracle's syntax. It's also simpler to build: no
  `this.`->`self.` action-code transform is needed (this grammar has no
  target-specific embedded actions at all) and no companion
  `*LexerBase.py`/`*ParserBase.py` superclass files are required.
- **A build quirk worth knowing**: `Db2Parser.g4` is a separate parser
  grammar (`options { tokenVocab=Db2Lexer; }`), not a combined
  lexer+parser file. Generating both together in one `antlr4` invocation
  fails with `cannot create implicit token for string literal in
  non-combined grammar` for punctuation the parser references by literal
  (`'('`, `'>'`, etc.) even though every one of those literals *is* a real
  named token in the lexer -- ANTLR needs `Db2Lexer.tokens` to already
  exist before it can resolve them. `build/generate_parser.sh` generates
  the lexer first, then the parser with `-lib` pointing at that output.
- **Generated code**: `src/metchurial/_generated/` (ANTLR codegen output from these `.g4`
  files) inherits the same MIT provenance; ANTLR's own codegen header
  comment ("Generated from Db2Parser.g4 by ANTLR 4.13.2") must be left
  intact, not stripped, including in the bundled `dist/` artifact.

## 2. `antlr4-python3-runtime` (`vendor/antlr4-python3-runtime/`)

- **Source**: [PyPI `antlr4-python3-runtime`](https://pypi.org/project/antlr4-python3-runtime/),
  version `4.13.2` (matches the ANTLR tool version used for codegen).
- **License**: BSD 3-Clause ("The ANTLR Project", 2012-2017). Confirmed via
  each source file's header comment and PyPI metadata (`License: BSD`,
  authors Terence Parr / Sam Harwell). Full text vendored verbatim at
  `vendor/antlr4-python3-runtime/LICENSE.txt`.
- **Modifications**: none — vendored as-is from the published wheel.
- **Why vendored rather than `pip install`ed at runtime**: the target
  company environment does not allow ad-hoc third-party package installs.
  The runtime is pure Python with no C extensions and no further
  dependencies, so it is safe to bundle directly into the single-file
  deployable artifact.

## Action item

Before `dist/metchurial.py` ships into the company's
restricted environment, have this file (and the two vendored LICENSE texts)
reviewed by whoever handles third-party-code intake there — vendoring into
an internal tool still counts as redistribution under both licenses.
