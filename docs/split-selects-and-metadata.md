# ANTLR, Split Selects, and Metadata Extraction

metchurial parses DB2 SQL with a real grammar, not regex — but "run
ANTLR's generated parser over the file" is not, by itself, enough to get
reliable results out of real-world legacy SQL. This document covers how
ANTLR is actually used here: the vendored grammar, why a single top-level
parse isn't reliable, the tiered chunk-by-chunk driver built on top of it,
and the two customized behaviors layered on that foundation — deciding
where one standalone SELECT block ends and another begins
(`--split-selects`), and extracting structural metadata like table usages
and JOIN relationships (`--extract-metadata`).

See [query-identity.md](query-identity.md) and
[query-similarity.md](query-similarity.md) for the identity/similarity
analyses built *on top of* the metadata extraction described here.

## The grammar and the generated parser

The grammar itself is not hand-written: it's IBM Db2 LUW SQL's grammar
from [`antlr/grammars-v4`](https://github.com/antlr/grammars-v4)'s
`sql/db2` directory, vendored at `vendor/grammars-v4/Db2Lexer.g4` /
`Db2Parser.g4`. ANTLR's code generator turns those `.g4` grammar files
into a Python lexer/parser/visitor (`src/metchurial/_generated/`):

- **`Db2Lexer`** turns raw source text into a token stream — one `Token`
  per keyword, identifier, literal, operator, and punctuation mark, plus
  comments and whitespace on a separate *hidden* channel (never seen by
  the parser, but still inspectable — this is how comment-aware
  sensitive-value detection and `has_cte`/`has_union`'s token-scans work).
- **`Db2Parser`** consumes that token stream according to the grammar's
  rules (`sql_statement`, `search_condition`, `predicate`, ...) and builds
  a parse tree — one typed `*Context` node per matched rule.
- **`Db2ParserVisitor`** is the generated base class for walking that
  tree. Every extraction pass in this codebase
  (`ExtractorVisitor`/`ReferenceVisitor`/`FunctionVisitor`/
  `_PredicateFactVisitor`/`_JoinPredicateVisitor`) is a small subclass that
  overrides just the `visitX` methods it cares about and calls
  `visitChildren` everywhere else — the standard ANTLR visitor pattern.

Regenerating this trio (`scripts/` — only needed after touching the
grammar itself) and how `dist/metchurial.py` inlines them into one
self-contained file is covered in the README's
["How the bundle works"](../README.md#how-the-bundle-works); this
document is about how the generated parser gets *used*, not how it's
built or packaged.

## Why not one whole-file parse?

The obvious approach — feed the whole file to `Db2Parser`'s top-level
`db2_file` rule and let ANTLR's default error recovery handle whatever
doesn't fit — is not reliable here. DB2 SQL pulled from a real legacy
codebase is routinely exported/kept as loose fragments, not complete,
individually-valid statements: a file might hold one bare `WHERE` clause
someone copied out of a larger query, a statement with a typo, or a
reserved-keyword-colliding identifier the grammar can't accept as written.
ANTLR's default recovery degrades unpredictably across a whole file once
it hits the first real error, and a single bad fragment early in a large
file could taint everything parsed after it.

Instead, `parsing/statement_driver.py` does three things:

1. **Lex the whole file once.** One token stream is the single source of
   truth for comment/live-code channel boundaries, regardless of what any
   later parse attempt does.
2. **Split into chunks at top-level `;`** (paren depth 0, tracked over
   default-channel tokens only — a stray `;` inside a malformed comment
   can't affect this split, since hidden tokens are skipped entirely).
3. **Run a tiered resync loop per chunk**, scoped so error recovery can
   never escape into a *different* top-level statement (the chunk's own
   token sub-stream has nothing outside itself to escape into).

### The tiered resync loop

| Tier | What it tries | When it fires |
|---|---|---|
| **1 — race** | `sql_statement()`, `search_condition()`, and a narrow token-scan fallback (`supplementary_checks.py`) are *all* attempted at the current position; whichever consumes the most tokens wins (ties go to the structural parses) | Every iteration, first |
| **2 — resync** | Parse `search_condition()` right after the next `WHERE`/`ON`/`HAVING`, or `sql_statement()` at the next nested `SELECT` — whichever comes first | Only if Tier 1 made zero progress |
| **3 — skip** | Advance exactly one token | Safety valve — guarantees the loop always terminates |

Racing all three Tier-1 candidates (rather than trying structural parses
first and falling back to the token-scan only on failure) matters
concretely: `ACCT_ID ('0000001')` has no grammar path at all, but
`sql_statement()` alone *does* accept the bare identifier `ACCT_ID` as a
trivially complete one-token statement. If that shorter match were
committed first, the token-scan would never get a chance to see
`ACCT_ID (` as the three-token unit it actually is. Racing by
consumed-token-count, not try-order, is what makes the token-scan win
correctly in that case.

Two ANTLR tuning choices make this loop viable at scale rather than
merely correct:

- **`predictionMode = SLL`** instead of ANTLR's default `LL`. The
  grammar's flat `predicate` rule has many alternatives sharing a long
  `expression` prefix, so default `LL` prediction falls back to
  full-context prediction per list element to resolve the ambiguity —
  fine for a handful of items, but a `WHERE col IN (...)` with tens of
  thousands of literals turns that into tens of thousands of full-context
  predictions: the difference between milliseconds and hours for one
  statement. `SLL` is strictly weaker only at *choosing between
  simultaneously-valid alternatives* (which doesn't affect what gets
  extracted here) — it never accepts input `LL` would reject.
- **`BailErrorStrategy`** instead of ANTLR's default recovery. `ok` is
  already `False` on any reported error, so whatever `DefaultErrorStrategy`
  would go on to do internally after the first error is guaranteed-discarded
  work — for a statement with many small internal mismatches, that
  discarded recovery work is exactly what turns one syntax error into
  thousands of token-by-token resync attempts.

Both choices are performance-only: the actual accept/reject decision, and
therefore what data gets extracted, is identical either way.

## Deciding a "select block" (`--split-selects`)

A **select block** is one semicolon-delimited top-level chunk (reusing
`chunk_ranges()`'s own splitting above) that starts with an optional
`WITH <cte-list>` prologue, then `SELECT`. `select/select_blocks.py`'s
`classify_chunk` decides this with a **purely token-level pass — no
parser involvement at all**: it checks what the chunk's first
default-channel token is, and if it's `WITH`, walks the CTE list
(tracking paren depth the same way `chunk_ranges` tracks it) to confirm
the list eventually reaches a `SELECT`. Any other leading token
(`INSERT`/`UPDATE`/`DELETE`/`CREATE`/... or a malformed `WITH` that never
reaches `SELECT`) is `False`.

Doing this at the token level rather than asking the parse tree "is this
a SELECT statement" matters for the same reason the tiered driver exists
at all: it has to give a correct answer *regardless of which tier the
driver eventually resolves this chunk at*, including a chunk the parser
can't build a clean tree for.

| Chunk (first real tokens) | `classify_chunk` result | Why |
|---|---|---|
| `SELECT a.id FROM t1 a;` | `True` | Opens directly with `SELECT` |
| `WITH cte AS (SELECT ...) SELECT * FROM cte;` | `True` | `WITH` → CTE list → reaches `SELECT` |
| `INSERT INTO t1 VALUES (1, 2);` | `False` | Doesn't open with `SELECT`/`WITH` |
| `WITH cte AS (SELECT ...) INSERT INTO t2 SELECT * FROM cte;` | `False` | `WITH`'s CTE list is followed by `INSERT`, not `SELECT` |

A CTE prologue and the `SELECT` that consumes it are always counted as
**one** block, never split apart — a `WITH` clause contains no top-level
`;`, so `chunk_ranges()` already guarantees they land in the same chunk by
construction.

Once every chunk in a file is classified, `select_block_ranges` returns
just the `True` ones, in source order. Under `--split-selects`, a file
with 2+ standalone SELECT blocks gets one `<stem>-NN<ext>` file written
per block (`write_split_files`), and the original is deleted — a file
with exactly one block is left alone (there's nowhere else for a lone
block to go; writing a `-01` copy would just duplicate the original under
a new name).

## Extracting metadata: table usages and JOIN relationships

Table/alias/JOIN discovery (`references/table_scan.py`) is, like
`classify_chunk`, a **separate token-scan pass that never touches the
parser** — for two concrete reasons:

1. It must work uniformly regardless of which tier the tiered driver
   resolved a given chunk at, across both comma-joins and ANSI
   `JOIN ... ON`/`USING` chains, with one mechanism instead of two.
2. **Schema-qualified names have no parse path in the vendored grammar.**
   `table_name`/`column_name` are always a single unqualified `id_ : ID`
   token — the grammar's `ID` token itself contains no dot. `SELECT * FROM
   schema1.table1;` parses with zero syntax errors, but the tree only
   ever captures `table_name=schema1`; `.table1` is silently left
   unconsumed in the token stream, since `sql_statement()` (what the
   tiered driver actually calls) is never EOF-anchored. This is a known,
   tracked grammar limitation (issue #1) — the token-scan works around it
   by reading the raw token sequence around a name instead of relying on
   the tree to have captured it correctly.

### Two-pass discovery

`scan_query_blocks` runs two coordinated passes over a chunk's tokens:

- **Pass A (`_discover_blocks`)** — an unconditional walk over *every*
  token that never skips anything. It pushes a new `QueryBlock` on each
  `SELECT`, tracks paren depth to know which block is innermost, and
  closes a block either when its enclosing paren closes (covers CTE
  bodies and derived-table subqueries alike — both are just "a `SELECT`
  one or more parens deeper than its sibling") or when a new `SELECT`
  appears at the same-or-shallower depth (covers `UNION`/`INTERSECT`/
  `EXCEPT` siblings). This guarantees a nested `SELECT` — inside a derived
  table, `IN(...)`/`EXISTS(...)`, or a CTE body — is always found,
  regardless of what Pass B does or doesn't skip past.
- **Pass B (`_populate_table_lists`)** — attaches each block's own
  `FROM`/`JOIN`/`UPDATE`/`INTO` table references and builds its
  alias→`TableRef` map. Unlike Pass A, this pass *is* free to skip a
  derived table's parens (to keep scanning for a following comma/JOIN
  sibling in the same table list) — nothing is lost by that skip, because
  the recursive call re-invokes Pass B scoped to exactly that derived
  table's own token range, using the same block map Pass A already built.

CTE names are tracked separately (`find_cte_names`) and never recorded as
real tables — `WITH cte AS (...) SELECT * FROM cte` must not report `cte`
in `refs_tables.tsv`. A CTE reference still becomes a real `TableRef`
(flagged `is_cte=True`) so it resolves via the alias map and can still
participate in a JOIN edge — needed for `query-identity.md`'s join-topology
signal, which does care whether an outer query joins to a CTE result.

### Resolving a qualified reference back to its real table

A later `field_reference` (`a.ACCT_ID`) needs to resolve `a` back to its
real table. `resolve_qualifier` finds the innermost `QueryBlock` whose
`[start_char, stop_char)` character range contains the reference's
position, and looks `a` up in that block's `alias_map`. It's keyed by
**character offset**, not token index, on purpose: token indices get
reassigned per `CommonTokenStream`/`ListTokenSource` (each chunk gets its
own), while `Token.start`/`.stop` character offsets are fixed at lex time
— the only safe key for matching a tree-walk finding in one stream back
to a token-scan-computed scope built from a different one.

### Deriving a JOIN's table pair correctly

A JOIN connector's table pair comes from its own `ON`/`USING` predicate's
qualifiers first (`_resolve_pair`), falling back to FROM-clause position
only if that doesn't resolve cleanly to exactly two distinct known
aliases. Position alone is not reliable for a "hub table" pattern:

```sql
FROM a JOIN b ON a.x = b.x JOIN c ON a.y = c.y
```

`c`'s join really connects to `a` (per its own `ON` clause), not to `b`,
its immediate FROM-list predecessor — a purely positional
`entries[k]`/`entries[k+1]` pairing would get this wrong.

### Two sources of JOIN edges, merged without double-counting

`references/relations.py` (the `--extract-metadata`
`refs_relations.tsv`/`refs_query_identity.tsv` join-topology source) draws
from two independent sources:

1. **Structural edges** from `table_scan.scan_join_edges` — every
   explicit `JOIN ... ON`/`USING`, *excluding* `COMMA` joins (which carry
   no predicate of their own in this source).
2. **"WHERE-IMPLICIT" edges** (`_JoinPredicateVisitor`, parse-tree based)
   — an ordinary binary comparison between two table/alias-qualified
   columns that resolve to two distinct real tables in the same query
   block. This is the *only* source for comma-joins (their real predicate
   lives in the `WHERE` clause, not the `FROM` list), and it also
   independently re-surfaces an explicit JOIN's own `ON`-clause comparison
   as an ordinary tree descendant.

Because source 2 re-finds an explicit JOIN's own `ON` predicate
independently, `engine.py`'s `pre_chunk_hook` dedupes: once a table pair
already has a structural edge (source 1) in a chunk, a WHERE-implicit edge
for that *same pair in the same chunk* is dropped, so an ordinary JOIN
isn't double-counted. A comma-joined pair with no `WHERE` condition
linking it at all (a rare, degenerate cross join) goes unrecorded
entirely — a documented limitation, not a silent wrong answer.

### Column and function references

Two more visitors round out `--extract-metadata`, both parser-tree based
(unlike the token-scan work above) and both **unconditional** — every
occurrence, not just ones inside a comparison:

- **`ReferenceVisitor`** (`references/reference_visitor.py`) walks every
  `column_name`/`field_reference` node and resolves each one to its owning
  `schema.table` via the same `resolve_qualifier` the predicate/relation
  visitors use.
- **`FunctionVisitor`** (`references/function_visitor.py`) records every
  function call and predicate operator actually used, with the exact
  source text of its arguments.

### Worked example: one file through the whole pipeline

Running full `--extract-metadata` extraction (table refs, column refs,
relations, functions) against this statement —

```sql
SELECT
    A.ACCT_ID,
    B.CTRT_NO,
    C.STAT_CD,
    D.TBSAMPLE001,
    CASE
        WHEN B.CTRT_TYPE_CD = '01' THEN B.BASE_AMT * 1.05
        WHEN B.CTRT_TYPE_CD = '02' THEN B.BASE_AMT * 1.10
        ELSE B.BASE_AMT
    END AS ADJ_AMT
FROM TBACCT A
INNER JOIN TBCTRT B
    ON A.ACCT_ID = B.ACCT_ID
LEFT OUTER JOIN TBSTAT C
    ON B.CTRT_NO = C.CTRT_NO
JOIN TBSAMPLE001 D
    ON A.ACCT_ID = D.ACCT_ID
WHERE C.STAT_CD IN ('01', '02')
  AND B.CTRT_TYPE_CD <> '99'
  AND A.OPEN_DT BETWEEN '20200101' AND '20261231'
GROUP BY A.ACCT_ID, B.CTRT_NO, C.STAT_CD, D.TBSAMPLE001, B.CTRT_TYPE_CD, B.BASE_AMT;
```

— the same base query [query-identity.md](query-identity.md) and
[query-similarity.md](query-similarity.md) use in their own worked
examples — produces (real output, not illustrative; line numbers assume
this statement starts at line 1 of its own file):

**`refs_tables.tsv`** (`table_uses`):

| schema | table | line |
|---|---|---|
| (no-schema) | TBACCT | 11 |
| (no-schema) | TBCTRT | 12 |
| (no-schema) | TBSTAT | 14 |
| (no-schema) | TBSAMPLE001 | 16 |

**`refs_relations.tsv`** (`relation_edges`):

| table_a | join_type | table_b | predicate | line |
|---|---|---|---|---|
| TBACCT | INNER | TBCTRT | `A.ACCT_ID = B.ACCT_ID` | 11 |
| TBCTRT | LEFT | TBSTAT | `B.CTRT_NO = C.CTRT_NO` | 12 |
| TBACCT | JOIN | TBSAMPLE001 | `A.ACCT_ID = D.ACCT_ID` | 11 |

**`refs_functions.tsv`** (`function_calls` — predicate operators count as
"function-shaped" usage here too):

| function | parameters | line |
|---|---|---|
| `=` | `A.ACCT_ID, B.ACCT_ID` | 13 |
| `=` | `B.CTRT_NO, C.CTRT_NO` | 15 |
| `=` | `A.ACCT_ID, D.ACCT_ID` | 17 |
| `IN` | `C.STAT_CD, ('01', '02')` | 18 |
| `<>` | `B.CTRT_TYPE_CD, '99'` | 19 |
| `BETWEEN` | `A.OPEN_DT, '20200101', '20261231'` | 20 |

**`refs_columns.tsv`** (`column_uses`, first few rows):

| schema | table | column | line |
|---|---|---|---|
| (no-schema) | TBACCT | ACCT_ID | 13 |
| (no-schema) | TBCTRT | ACCT_ID | 13 |
| (no-schema) | TBCTRT | CTRT_NO | 15 |
| (no-schema) | TBSTAT | CTRT_NO | 15 |

Every one of these rows traces back to the same two-pass token-scan
(`scan_query_blocks`) plus the parser-tree visitors described above,
all run once per chunk inside the same tiered resync loop — one parse
pipeline feeding sensitive-value detection, select-block splitting, and
every `--extract-metadata` output alike.

## Known limitations

- **3-part catalog-qualified names** (`catalog.schema.table`) drop the
  catalog segment — only the trailing `schema.table` is kept.
- **Reserved-keyword-colliding aliases** (a table aliased `s`, a single
  reserved letter token; a CTE named `base`, a reserved word) are still
  recognized by the token-scan (position is the structural signal, not a
  token-type whitelist), but can still make the *parser* fail to build one
  clean tree for the statement — which is exactly what the tiered driver's
  Tier 2/3 resync exists to route around, at the cost of a coarser
  signature for that one statement (see
  [query-identity.md](query-identity.md)'s known limitations).
- **A comma-joined pair with no linking `WHERE` condition** goes
  unrecorded as a relationship entirely (see "Two sources of JOIN edges"
  above).
