# Third-party provenance

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
  change, not a new token. `Db2Lexer.g4` is unmodified. This is called out
  here per the file actually having changed, not as a formality --
  `tests/test_grammar_smoke.py`'s `TestFetchRowLimiting` pins down both
  forms parsing identically.
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
- **Generated code**: `generated/` (ANTLR codegen output from these `.g4`
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
