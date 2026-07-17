# metchurial

An ANTLR-backed static analysis engine for DB2 SQL: it parses SQL source
into a real syntax tree — not regex — using
[`antlr/grammars-v4`](https://github.com/antlr/grammars-v4)'s `sql/db2`
grammar, a purpose-built IBM Db2 LUW SQL grammar, and turns that tree into
structured, queryable metadata: every table, column, function, and
predicate reference a file makes, and the JOIN relationships between
tables, aggregated across an entire codebase. Legacy enterprise SQL is
itself a dataset worth analyzing systematically, not just code to review
file by file — that's what this toolkit is for. Hardcoded-sensitive-value
detection, SELECT-block splitting, and literal masking are all built on
that same parse tree, as specific analyses layered on top of it.

## Capabilities

| Capability | Flag | Details |
|---|---|---|
| **Metadata extraction** — every table/column/function/predicate reference, JOIN relationships aggregated across the whole scan | `--extract-metadata` | [What it extracts](#what-it-extracts) |
| **Sensitive-value detection** — sensitive-column comparisons and known-name literals | *(default, always on)* | [What it detects](#what-it-detects) |
| **File splitting** — one file per standalone SELECT block | `--split-selects` | [Output artifacts](#output-artifacts) |
| **Literal masking** — rewrite flagged literals to fixed placeholders in place | `--mask-literals` | [Output artifacts](#output-artifacts) |

## Quick start

You only need **one file**: `dist/metchurial.py`. It's a
self-contained bundle — the generated Db2 SQL parser and the ANTLR Python
runtime are both inlined into it, so it runs with plain `python` and no
`pip install`. This is verified in CI by running it in a virtualenv with
zero third-party packages installed (not even `antlr4-python3-runtime`)
and diffing the output against a normal run — see `tests/test_bundle.py`.

```bat
python metchurial.py C:\sql\root
python metchurial.py C:\sql\root --sensitive-columns ACCT_ID CTRT_NO HLDR_NM
python metchurial.py C:\sql\root --extract-metadata --split-selects
python metchurial.py C:\sql\root --mask-literals
python metchurial.py C:\sql\root --workers 8 --verbose
```

Every run writes its artifacts (`summary.md`, `findings.tsv`, ...) into the
**current working directory**, not the scan root — see
[Output artifacts](#output-artifacts) below. Exit code is `1` if anything
was found (FINDING), `0` if clean — convenient for wiring into a CI
step or a pre-commit check.

**Before carrying `dist/metchurial.py` into a restricted
environment**, read [How the bundle works](#how-the-bundle-works) below and
get `docs/PROVENANCE.md` reviewed by whoever handles third-party-code
intake there.

### Running from source with uv

If you have [uv](https://docs.astral.sh/uv/) and don't need the
zero-dependency single-file artifact, you can run straight from source
instead of `dist/metchurial.py`:

```bash
uv sync
uv run metchurial /sql/root
uv run metchurial /sql/root --extract-metadata --split-selects
```

`uv sync` pulls in just the one runtime dependency this needs
(`antlr4-python3-runtime`, exact-pinned to match the version `generated/`'s
parser was built with) into a project-local `.venv` — no Java, no ANTLR
tooling required for that (those are dev-only, for regenerating
`generated/` or rebuilding `dist/metchurial.py` itself — see
[Dev workflow](#dev-workflow)).

## CLI reference

| Flag | Default | Description |
|---|---|---|
| `root` (positional) | — | Directory to scan recursively |
| `--sensitive-columns` | `ACCT_ID CTRT_NO ACCT_NM ACCT_NAME` | Column names sensitive-column comparison detection treats as sensitive; fully replaces the default list, doesn't add to it |
| `--extensions` | `sql txt` | File extensions to scan, without the dot |
| `--extract-metadata` | off | Also emit `refs_tables.tsv`/`refs_columns.tsv`/`refs_functions.tsv`/`refs_relations.tsv` (schema/table/column refs, JOIN relationships, function/predicate usage) and matching summary.md sections — see [Output artifacts](#output-artifacts) |
| `--split-selects` | off | For a file with 2+ standalone SELECT blocks, write one `<stem>-NN<ext>` file per block alongside the original (files with a single block are left as-is) |
| `--mask-literals` | off | Rewrite in place every flagged literal's content to a fixed placeholder (`'****'`/`"****"` for quoted, `0000` for unquoted numeric), everything else byte-for-byte identical — back up files first, this overwrites them |
| `--workers N` | `1` | Scan across N worker processes instead of one |
| `--max-chunk-iterations N` | `200000` | Safety-valve cap on the resync driver's loop iterations per statement chunk |
| `--verbose` | off | Print a `[i/N]` progress line to stderr as each file is scanned |

`--workers N` scans files across N worker processes (`concurrent.futures.
ProcessPoolExecutor`, stdlib only). Parsing is CPU-bound pure Python, so
this is real multi-core parallelism, not threads, which the GIL would keep
from helping here. Each file is scanned independently with no shared
state, so results are unaffected other than which order they're merged in
(the reports already group/sort by file and line regardless). Leave a
couple of cores free for the OS/other work rather than setting `--workers`
to your full core count.

## What it extracts

`--extract-metadata` walks the same parse tree detection uses, but
unconditionally — every reference in the file, not just ones compared to a
literal — and resolves each one back to the table/schema it actually
belongs to:

- **Table & schema references** — every `schema.table` a file's SQL
  touches. Each query block gets its own alias map, so a bare `t1` or
  `t1.col` resolves back to the schema-qualified table it actually refers
  to, not just the identifier as written on that line.
- **Column references** — every `schema.table.column` reference in the
  file, not only ones inside a comparison; a correlated subquery's own
  `t.col` is resolved within its own scope, not leaked into its parent's.
- **Function & predicate usage** — every function call (`SUBSTR`,
  `COALESCE`, `SUM`, ...) and predicate operator (`=`, `IN`, `BETWEEN`,
  `LIKE`, `IS NULL`, ...) actually used, with the exact source text of its
  arguments/operands.
- **JOIN relationships** — every table-to-table JOIN edge, aggregated
  across the *entire scan* (one graph, not one per file) — how tables in a
  legacy schema actually connect in practice, not what an ER diagram
  claims they should.

Each of these lands in its own `refs_*.tsv` — see
[Output artifacts](#output-artifacts) — built to be loaded straight into a
spreadsheet or a graph tool.

## What it detects

Sensitive-value detection is one specific analysis built on the same parse
tree metadata extraction uses — always on, independent of
`--extract-metadata`. It's two independent mechanisms, each producing its
own finding:

- **Sensitive-Column Comparison Detection — FINDING**: a sensitive column
  (see `--sensitive-columns`) compared to a hardcoded literal — `=`, `<>`,
  `!=`, `<=`, `>=`, `<`, `>`, `(NOT) IN (...)`, `(NOT) LIKE`,
  `BETWEEN ... AND ...`, or a bare `(` before a literal (a DB2 quirk) — in
  either direction and regardless of spacing or line breaks.
- **Known-Name Matching — FINDING**: any quoted, name-shaped literal (2-4
  Hangul syllables) whose text is listed in `known_names.txt`, regardless
  of which column it's compared to. There's no surname heuristic — a
  literal only becomes a finding once a human has confirmed it's a real
  name. Every other name-shaped literal is a triage *candidate*: it shows up
  in `strings.txt` each run until it's copied into either `known_names.txt`
  (flags it as a finding from then on) or `stopwords.txt` (excludes it from
  `strings.txt` from then on). Both files are one word per line, `#`
  comments allowed, auto-created empty on first run — see
  [Output artifacts](#output-artifacts).

Findings inside `--`/`/* */` comments are still reported (commented-out
code can leak real data) and tagged `in_comment=Y` in `findings.tsv`.
`/* */` comments may nest, and a finding inside a nested comment is still
found.

### Public placeholder names

The column and table names used throughout this repo — `ACCT_ID`,
`CTRT_NO`, `ACCT_NM`, `ACCT_NAME`, `HLDR_NM`, `TBSAMPLE001`, `STAT_CD` —
are placeholders, not real production schema names from any actual DB2
environment, swapped in consistently before this repo was made public.
They appear in `DEFAULT_COLUMNS` (`src/scan.py`, `--sensitive-columns`'s
built-in default), every fixture under `tests/fixtures/`, and this
README's own examples. This doesn't affect behavior — `--sensitive-columns`
always fully replaces the default list, so a real deployment should pass
its own actual column names explicitly on every run rather than relying on
the shipped defaults meaning anything for your schema.

## Output artifacts

Every scan writes the same fixed set of files into the current working
directory (not the scan root, and not configurable — one predictable set
of names regardless of invocation). `summary.md` is an index into the
others: bounded counts and top-N tables with pointers to the full detail,
not a duplicate of it.

| File | Written when | Contents |
|---|---|---|
| `summary.md` | always | Run info, Sensitive Findings (with per-file detail), String Occurrences, Bad Files, Stopwords, Known Names, and — if enabled — Table & Column References, Functions, Relations, Select Blocks |
| `findings.tsv` | always | Every finding, one row per literal, for filtering/sorting in Excel |
| `strings.txt` | always | Unique name-shaped literals not yet classified into `known_names.txt`/`stopwords.txt`, with occurrence counts, in a format directly copy-pasteable into either |
| `stopwords.txt` | always (auto-created empty with a format header if missing) | Name-shaped literals reviewed and confirmed *not* sensitive — excluded from `strings.txt` from then on; edit in place |
| `known_names.txt` | always (auto-created empty with a format header if missing) | Name-shaped literals reviewed and confirmed sensitive — every matching literal becomes a known-name finding from then on; edit in place |
| `bad_files.txt` | always | Persistent skip-list of files too malformed to parse — see [Bad files](#bad-files) |
| `refs_tables.tsv` | `--extract-metadata` | Every `schema.table` reference found, with file/line |
| `refs_columns.tsv` | `--extract-metadata` | Every `schema.table.column` reference found, with file/line |
| `refs_functions.tsv` | `--extract-metadata` | Every function call and predicate operator found, with operands/file/line |
| `refs_relations.tsv` | `--extract-metadata` | Table-to-table JOIN usage aggregated across the whole scan (one file, not per-directory) |

## Bad files

Some real-world SQL files aren't really valid SQL — internal section
dividers (`========`, `<<목표KPI>>`), bare prose headers, Korean-language
comments used as informal headings, or files with the actual SQL truncated
partway through. These can make the parser resync loop grind for a very
long time on a single file, or crash it outright.

Two independent safety nets guard against this:

- A cheap **pre-check** on the token stream (lexer-error ratio and
  long runs of repeated punctuation) flags a file as bad before any real
  parsing is attempted.
- A broad **try/except** around the actual scan of each file catches any
  unexpected crash and treats it the same way.

Either path records the file's path and a short reason in `bad_files.txt`,
and the file is skipped entirely — not even attempted — on every later
run. Workflow:

1. Run the scan; anything unfixably weird lands in `bad_files.txt` and is
   skipped from then on.
2. Fix the file's SQL content by hand (or decide it's fine to leave out).
3. Delete that file's line from `bad_files.txt`.
4. Re-run — the file is attempted again on the next scan.

`bad_files.txt` is a local, per-environment artifact (it's `.gitignore`d)
rather than something meant to be committed and shared.

## Known limitations

Known gaps in the vendored grammar, `--extract-metadata` extraction, and
the file-encoding auto-detection are tracked as GitHub issues, not
duplicated here — refer to
[Issues](https://github.com/CynicDog/metchurial/issues). Each is backed
by a runnable test (`tests/test_grammar_smoke.py`,
`tests/test_db2_grammar_specific_cases.py`, and friends), not just prose.

## How the bundle works

`dist/metchurial.py` is built with
[stickytape](https://github.com/mwilliamson/stickytape), which inlines
every module's source as embedded strings. **At every run**, it writes
that source out to a fresh OS temp directory, imports from there, and
deletes it on exit. Practically:

- It needs write access to the OS temp directory (normally fine, but worth
  confirming in advance).
- Some corporate EDR/antivirus tools are wary of "a script writes many
  `.py` files to temp and imports them" as a pattern. If your environment
  has an infra security review step, flag this mechanism to them up front
  — `docs/PROVENANCE.md` documents exactly what's bundled and why.

The file is large (~4.8MB, mostly the Db2 parser's serialized ATN tables)
-- one file, but not a small one, and not realistically human-auditable
top to bottom.

## Dev workflow

Everything below needs the dev dependency group (`antlr4-tools`,
`stickytape`, `ruff` — see `pyproject.toml`) plus Java for grammar
regeneration specifically (`uv`/`pip` can't install that) — none of this
runs in the restricted target environment; only `dist/metchurial.py` does.

```bash
uv sync

# regenerate generated/ from vendor/grammars-v4/*.g4 (only needed after
# touching the grammar itself)
uv run bash build/generate_parser.sh

# run everything: grammar smoke tests, scan_file()-level tests, end-to-end
# edge-case regressions, and the bundle self-containment check
uv run python -m unittest discover -s tests -p "test_*.py"

# lint
uv run ruff check src

# rebuild the deployable single-file artifact
uv run python build/bundle.py
```

## Licensing

This project vendors two pieces of third-party code into the deployable
artifact: an IBM Db2 SQL grammar (MIT, from `antlr/grammars-v4`'s
`sql/db2`) and `antlr4-python3-runtime` (BSD-3-Clause). See
`docs/PROVENANCE.md` for exact versions, license texts, and what (if
anything) was modified.
