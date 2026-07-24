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
| **Un-split** — best-effort revert of a previous `--split-selects` run, from `split_manifest.tsv` | `--un-split-selects` | [CLI reference](#cli-reference) |
| **Literal masking** — rewrite flagged literals to fixed placeholders in place | `--mask-literals` | [Output artifacts](#output-artifacts) |
| **Quarantine** — move every non-matching-extension file to `_quarantine/excluded/` before scanning, and every file that fails to parse to `_quarantine/bad_files/` after | *(always on, automatic)* | [Quarantine](#quarantine) |

## Quick start

You only need **one file**: `dist/metchurial.py`. It's a
self-contained bundle — the generated Db2 SQL parser and the ANTLR Python
runtime are both inlined into it, so it runs with plain `python` and no
`pip install`. This is verified in CI by running it in a virtualenv with
zero third-party packages installed (not even `antlr4-python3-runtime`)
and diffing the output against a normal run — see `tests/test_bundle.py`.

```bat
python metchurial.py C:\sql\root --help 
python metchurial.py C:\sql\root --sensitive-columns ACCT_ID CTRT_NO HLDR_NM --extract-metadata

python metchurial.py C:\sql\root `
    --sensitive-columns ACCT_ID CTRT_NO HLDR_NM `
    --max-chunk-iterations 5000000 `
    --workers 8 `
    --extract-metadata `
    --verbose

python metchurial.py C:\sql\root `
    --workers 8 `
    --split-selects `
    --verbose

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
(`antlr4-python3-runtime`, exact-pinned to match the version `src/metchurial/_generated/`'s
parser was built with) into a project-local `.venv` — no Java, no ANTLR
tooling required for that (those are dev-only, for regenerating
`src/metchurial/_generated/` or rebuilding `dist/metchurial.py` itself — see
[Dev workflow](#dev-workflow)).

### Installing from PyPI

```bash
pip install metchurial
```

### Installing with uv

```bash
uv add metchurial
```

Either installs the `metchurial` CLI and the library API below. The
single-file `dist/metchurial.py` remains the distribution channel for
restricted environments where even `pip install` isn't an option.

### Using as a library

The CLI is one consumer of a plain Python API — install the package and
drive scans from your own code:

```python
import metchurial

# One call: scan a tree with every metadata analysis on.
result = metchurial.scan("/sql/root", metchurial.ScanOptions.metadata())

for f in result.findings:                       # sensitive-value findings
    print(f.file, f.line, f.column_name, f.value)
for row in result.identity_rows:                # per-statement core_ids
    print(row.core_id, row.file, row.line)

# Or per-file, with only what you need switched on:
one = metchurial.scan_file(
    "query.sql",
    metchurial.ScanOptions(sensitive_columns=("ACCT_ID", "HLDR_NM"),
                           extract_relations=True))
```

`scan()`/`scan_file()` return typed result objects
(`TreeScanResult`/`FileScanResult` of `Finding`/`TableUse`/`RelationEdge`/
`IdentityRow`/... rows) and never print or write files on their own —
report artifacts (`summary.md`, `findings.tsv`, `refs_*.tsv`) are the
CLI's job. The one exception is `ScanOptions(split_selects=True)`, which
writes `-NN` split files next to each multi-SELECT source file and deletes
the original, same as the `--split-selects` flag. Everything a scan can be told is a field on
`ScanOptions` (a frozen dataclass); `ScanOptions.metadata()` is shorthand
for switching every `extract_*` analysis on, mirroring
`--extract-metadata`.

## Workflow

metchurial is built to be run repeatedly, with a human triaging its output
between runs — it deliberately doesn't try to auto-decide which name-shaped
literals are sensitive or which unparseable files are safe to ignore.

1. **Run it.** A first run over a fresh root produces `strings.txt` (every
   name-shaped literal not yet classified, with occurrence counts). Every
   run also, automatically, moves any non-matching-extension file to
   `_quarantine/excluded/` and any file that fails to parse to
   `_quarantine/bad_files/` — see [Quarantine](#quarantine) — with
   `bad_files.tsv` recording the reason for each.
2. **Triage `strings.txt`.** Go through it and, for each candidate:
   - a real name you consider sensitive → copy it into `known_names.txt`;
     every literal matching it becomes a Known-Name-Matching finding from
     then on.
   - an ordinary word that just happens to be name-shaped (2-4 Hangul
     syllables) but isn't a name → copy it into `stopwords.txt`; it drops
     out of `strings.txt` from then on.

   A candidate left in neither file keeps reappearing in `strings.txt`
   every run until you classify it one way or the other.
3. **Triage `bad_files.tsv`.** For each file listed, open it at its
   `quarantined_file` path (it's no longer at its original location —
   see [Quarantine](#quarantine)), fix whatever made it unparseable (or
   decide it's fine to leave out), then move it back to somewhere under
   `root` matching `--extensions` and delete that file's data row (keep
   the header row) to mark it for another attempt.
4. **Re-run.** Names now in `known_names.txt`/`stopwords.txt` change
   what's a finding and what still shows up in `strings.txt`; a file put
   back in `root` after its `bad_files.tsv` row was deleted gets parsed
   again and either scans clean or lands back in the list (and back in
   `_quarantine/bad_files/`) with a reason.
5. Repeat steps 2-4 until `strings.txt` has nothing left to classify and
   `bad_files.tsv` has no rows left, or only rows for files you've
   deliberately decided to leave out of scanning.

## CLI reference

Running `metchurial` with no arguments at all launches an interactive
wizard instead of argparse's usual "the following arguments are required"
error — it prompts for every flag below in turn (blank answer = default),
prints the equivalent command line once you're done answering, then runs
that scan. Useful for a first run or occasional use; scripts/CI should
keep passing flags directly, which skips the wizard entirely and behaves
exactly as before.

| Flag | Default | Description |
|---|---|---|
| `root` (positional) | — | Directory to scan recursively |
| `--sensitive-columns` | `ACCT_ID CTRT_NO ACCT_NM ACCT_NAME` | Column names sensitive-column comparison detection treats as sensitive; fully replaces the default list, doesn't add to it |
| `--extensions` | `sql txt` | File extensions to scan, without the dot. Same-directory files that reduce to the same name once backup-style extensions are stripped (`query1.sql` / `query1.sql.bak`, or a lone `query1.bak`) count as one file, not two — unless their content actually differs, in which case both are scanned |
| `--extract-metadata` | off | Also emit `refs_tables.tsv`/`refs_columns.tsv`/`refs_functions.tsv`/`refs_relations.tsv`/`refs_query_identity.tsv` (schema/table/column refs, JOIN relationships, function/predicate usage, per-statement structural identity) and matching summary.md sections — see [Output artifacts](#output-artifacts) |
| `--identity-granularity` | `structure` | Which structural fact categories discriminate a statement's `core_id`, loosest to strictest: `table` (table set only) → `structure` (+ join types/relationships/query shape — the original, still-default behavior) → `filtered` (+ WHERE predicates) → `strict` (+ GROUP BY, i.e. the full fact set). See [docs/query-identity.md](docs/query-identity.md). Requires `--extract-metadata` unless left at its default |
| `--query-similarity` | off | Also emit `refs_query_similarity.tsv`: pairwise Jaccard similarity between statements that don't share a `core_id`. Opt-in because the pass is O(n²) in the number of *distinct* core_ids — fine for thousands of distinct queries, slow for tens of thousands. Requires `--extract-metadata` |
| `--split-selects` | off | For a file with 2+ standalone SELECT blocks, write one `<stem>-NN<ext>` file per block alongside the original, then delete the original and record the mapping in `split_manifest.tsv` (files with a single block are left as-is). Only safe to run against a tree you already have a separate copy of |
| `--un-split-selects` | off | Before scanning, reverts a previous `--split-selects` run using `split_manifest.tsv`: for each `original_file` it records, if every one of its split files is still present and `original_file` hasn't been recreated since, concatenates the split files' *current* content back together (block order) into `original_file` and deletes the split files. Best-effort, not a byte-for-byte undo — the original inter-statement whitespace was already discarded at split time. A group missing a split file, an incomplete group, or one whose `original_file` already exists again is left alone and stays in `split_manifest.tsv`. Mutually exclusive with `--split-selects` |
| `--mask-literals` | off | Rewrite in place every flagged literal's content to a fixed placeholder (`'****'`/`"****"` for quoted, `0000` for unquoted numeric), everything else byte-for-byte identical — back up files first, this overwrites them |
| `--workers N` | `1` | Scan across N worker processes instead of one |
| `--max-chunk-iterations N` | `200000` | Safety-valve cap on the resync driver's loop iterations per statement chunk |
| `--verbose` | off | Also print a one-line ANTLR processing summary (chunk count, tiered-loop iteration breakdown, elapsed time) to stderr after each file's `[i/N]` progress line, which itself is always printed regardless of this flag. Also adds a reason line under each `[quarantine:excluded]`/`[quarantine:bad_file]` stderr line (see [Quarantine](#quarantine)) |

There is no flag to turn quarantining on or off: every run automatically
moves non-matching-extension files to `_quarantine/excluded/` and
files that fail to parse to `_quarantine/bad_files/` — see
[Quarantine](#quarantine). There is likewise no incremental/caching
flag — every run does a full, fresh scan.

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
  either direction and regardless of spacing or line breaks. Also covers
  the two non-comparison shapes a sensitive column's literal commonly
  takes outside a WHERE/ON/HAVING clause: `UPDATE ... SET SENSITIVE_COL =
  'literal'` (an assignment, not a comparison — its own grammar rule,
  visited independently) and `INSERT INTO t (SENSITIVE_COL, ...) VALUES
  ('literal', ...)` (bound to its column by position against an *explicit*
  column list — a schema-less `INSERT INTO t VALUES (...)` with no column
  list is never guessed at, since there's no DDL here to know the real
  column order). **Known gap:** the vendored grammar currently can't parse
  the explicit-column-list `INSERT` shape at all (`no viable alternative`,
  even though `INSERT INTO t VALUES (...)` with no column list parses
  fine) — see `tests/test_scan.py`'s `TestInsertValuesDetection` for the
  reproduction; until that's worked around, a sensitive literal in that
  specific shape produces no finding.
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
They appear in `DEFAULT_SENSITIVE_COLUMNS` (`src/metchurial/models/options.py`, `--sensitive-columns`'s
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
| `summary.md` | always | Run info; if `--extract-metadata` is on, Query Identity, Relations, Functions, Table & Column References; String Occurrences, Bad Files, Stopwords, Known Names; if `--split-selects` is on, Select Blocks; and finally Sensitive Findings (with per-file detail) |
| `findings.tsv` | always | Every finding, one row per literal, for filtering/sorting in Excel |
| `strings.txt` | always, full rewrite | Unique name-shaped literals — from live code and commented-out code alike — not yet classified into `known_names.txt`/`stopwords.txt`, most-frequent-first with occurrence counts, in a format directly copy-pasteable into either. Recomputed from scratch every run (not merged with past runs), so an unclassified literal just keeps reappearing until you triage it |
| `stopwords.txt` | only if missing | Name-shaped literals reviewed and confirmed *not* sensitive — excluded from `strings.txt` from then on. Auto-created empty with a format-header if it doesn't exist yet; never rewritten by the tool otherwise, so it's safe to edit in place |
| `known_names.txt` | only if missing | Name-shaped literals reviewed and confirmed sensitive — every matching literal becomes a known-name finding from then on. Auto-created empty with a format-header if it doesn't exist yet; never rewritten by the tool otherwise, so it's safe to edit in place |
| `bad_files.tsv` | always, merged with past runs | Persistent record of files that matched `--extensions` and were actually attempted, but too malformed to parse — one row per file (original path, category, item, reason, quarantined-to path), tab-separated. Each run's newly-flagged files are physically moved to `_quarantine/bad_files/` (see [Quarantine](#quarantine)) and added to whatever was already listed, so entries survive until you delete their row — see [Bad files](#bad-files). Not to be confused with `quarantine_manifest.tsv` below, whose files were never attempted at all |
| `refs_tables.tsv` | `--extract-metadata` | Every `schema.table` reference found, with file/line |
| `refs_columns.tsv` | `--extract-metadata` | Every `schema.table.column` reference found, with file/line |
| `refs_functions.tsv` | `--extract-metadata` | Every function call and predicate operator found, with operands/file/line |
| `refs_relations.tsv` | `--extract-metadata` | Every table-to-table JOIN edge found, one row per occurrence, with join type/predicate/file/line. The cross-file table-pair rollup (grouped by table_a/table_b with a join count) is summary.md's own "## Relations" section, not this file |
| `refs_query_identity.tsv` | `--extract-metadata` | One `core_id` per statement — structurally identical statements share one id regardless of aliasing/projection/formatting differences |
| `refs_query_similarity.tsv` | `--query-similarity` | Pairwise Jaccard similarity between distinct `core_id`s that don't match exactly |
| `split_manifest.tsv` | `--split-selects` | One row per split file actually written: `original_file`, `split_file`, `block_number`, `total_blocks` -- the record of which now-deleted original each split file came from. `--un-split-selects` reads this same file to revert, then rewrites it keeping only the rows it couldn't revert |
| `quarantine_manifest.tsv` | always | One row per non-matching-extension file moved to `_quarantine/excluded/`: `original_file`, `quarantined_file` — see [Quarantine](#quarantine) |

## Quarantine

Every run, automatically — no flag turns this on or off — physically
moves two kinds of file out of the scanned tree and into `_quarantine/`,
so that after a run, everything left under `root` is exactly what was
actually scanned, and everything that wasn't (or that was but couldn't be
made sense of) is sitting somewhere else, still on disk, never deleted:

```
_quarantine/
├── excluded/    <- non-matching-extension files (quarantine.extensions)
└── bad_files/   <- files that failed to parse (quarantine.bad_files)
```

- **`_quarantine/excluded/`** — before the scan starts, every file under
  `root` whose extension isn't in `--extensions` is moved here, mirroring
  its path relative to `root` (`sub/notes.docx` →
  `_quarantine/excluded/sub/notes.docx`). It's never opened, let alone
  parsed — this doesn't change what gets scanned, since the scan only
  ever looked at `--extensions` files anyway, it just clears everything
  else out of the tree first. `quarantine_manifest.tsv` records one row
  per file moved.
- **`_quarantine/bad_files/`** — once the scan finishes, every file it
  flagged bad *this run* (see [Bad files](#bad-files) below for what that
  means) is moved here the same way. `bad_files.tsv` keeps its row —
  original path, category, reason, **and** the `quarantined_file` path it
  now lives at — rather than deleting it, so the historical record
  survives the move.

`_quarantine/` itself is always excluded from the scan's own directory
walk, on every run, whether or not it happens to sit inside `root` — a
bad file quarantined there on a previous run has a matching extension by
definition, so without this it would be walked right back into and
rescanned as if it were fresh input.

Every file actually moved is logged to stderr as it happens —
`[quarantine:excluded] <original> -> <destination>` or
`[quarantine:bad_file] <original> -> <destination>` — one line per file,
always. `--verbose` adds a second, indented line under each: the
extension that excluded it, or the bad-file category/reason.

Nothing that ends up in `_quarantine/excluded/` can ever appear in
`bad_files.tsv`, and nothing that ends up in `_quarantine/bad_files/` can
ever appear in `quarantine_manifest.tsv` — the two mechanisms are
mutually exclusive by construction: one only ever looks at extension, the
other only ever runs on a file that already matched `--extensions` and
was actually attempted.

`_quarantine/` (like `bad_files.tsv`, `strings.txt`, etc.) is a local,
per-environment artifact, not something meant to be committed and shared.

## Bad files

**Bad files are strictly a subset of `--extensions`-matching files** —
every file scan_file() ever looks at has already passed the
`--extensions` filter, so "bad" is never about extension, only about what
happened once the scan actually opened, lexed, and tried to parse the
file. See [Quarantine](#quarantine) above for the opposite case, and for
what happens to a file once it's flagged bad here.

Some real-world SQL files aren't really valid SQL — internal section
dividers (`========`, `<<목표KPI>>`), bare prose headers, Korean-language
comments used as informal headings, or files with the actual SQL truncated
partway through. These can make the parser resync loop grind for a very
long time on a single file, or crash it outright.

Two independent safety nets guard against this:

- A cheap **pre-check** on the token stream flags a file as bad before any
  real parsing is attempted, under one of two categories:
  - `repeated-char-run` — a long run of identical single-character
    punctuation tokens in a row (`========`, `<<<<<<<<`), possibly spaced
    out (`- - - - -`). Tokens separated only by text a lexer error
    swallowed (e.g. bare, unquoted Korean prose sitting directly in the
    file body) are *not* treated as adjacent just because nothing sits
    between them in the token list — otherwise ordinary Korean sentences
    (each period landing right after the last, once the untokenizable
    words between them vanish) would look exactly like a divider. A
    single token that happens to be one long repeated character (a bare
    `3333333333333333`, or the same thing quoted) is deliberately *not*
    flagged either way — masked/dummy/round-number literals are
    completely ordinary SQL data, and unlike `========` a single token is
    cheap for the parser to fail on regardless of its content, so there's
    no actual performance problem to defend against.
  - `lexer-error-ratio` — too high a fraction of tokens are lexer errors
    (bare non-ASCII section headers or prose mixed directly into the file
    body rather than inside a comment). Deliberately tolerant of files
    that just use bare Korean column aliases extensively, a real and
    common pattern on its own.
- A broad **try/except** around the actual scan of each file catches any
  unexpected crash (`crash`) or unreadable file (`unreadable`) and treats
  it the same way.

Every path records the file's original path, category, the actual
offending value/snippet, and a full reason in `bad_files.tsv` — and the
file itself is physically moved to `_quarantine/bad_files/` (see
[Quarantine](#quarantine) above), not just recorded and left in place. On
every later run it's skipped entirely — not even attempted — since it no
longer sits at its original path anyway; putting it back up for another
attempt means fixing it at its `quarantined_file` path, moving it back to
somewhere under `root` matching `--extensions`, and deleting its data row
(keeping the header row) so the next scan picks it up fresh. See
[Workflow](#workflow) above for how this fits into the full triage loop.

`bad_files.tsv` is a local, per-environment artifact (it's `.gitignore`d)
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

# regenerate src/metchurial/_generated/ from vendor/grammars-v4/*.g4 (only needed after
# touching the grammar itself)
uv run bash build/generate_parser.sh

# run everything: grammar smoke tests, scan_file()-level tests, end-to-end
# edge-case regressions, and the bundle self-containment check
uv run python -m unittest discover -s tests -p "test_*.py"

# lint
uv run ruff check src

# rebuild the deployable single-file artifact
uv run python build/bundle.py

# build the PyPI sdist+wheel (kept out of dist/, which holds the bundle)
uv build --out-dir pypi-dist
```

Publishing to PyPI is automated: publishing a GitHub release triggers
`.github/workflows/publish.yml`, which builds and uploads via PyPI
trusted publishing — no API tokens involved.

## Licensing

This project vendors two pieces of third-party code into the deployable
artifact: an IBM Db2 SQL grammar (MIT, from `antlr/grammars-v4`'s
`sql/db2`) and `antlr4-python3-runtime` (BSD-3-Clause). See
`docs/PROVENANCE.md` for exact versions, license texts, and what (if
anything) was modified.
