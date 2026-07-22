# Query Identity (`core_id`)

`--extract-metadata` assigns every SQL statement a `core_id`: a short,
deterministic hash of that statement's structural signature. Statements
that are the same underlying query — differing only in things like
aliasing, which columns get selected, or how a derived column is
calculated — collapse onto the same `core_id`. Statements that touch
different tables, or join them differently, get different ones.

This document covers *why* `core_id` exists, exactly what it hashes, and
worked examples (with real, computed values from this repo's own test
fixtures) showing how a change to a query's SQL does or doesn't move its
`core_id`. See [query-similarity.md](query-similarity.md) for the
companion feature that scores statements which *don't* share a `core_id`
against each other, and the last section below for how the two relate.

## Purpose

A legacy DB2 codebase can hold thousands of `.sql` files. In practice,
many of them are not thousands of distinct queries — they're the same
handful of report/extract queries, copy-pasted and lightly edited over
years: an alias renamed, one extra column added to the SELECT list, a
narrower WHERE clause for a one-off run. Treating each file as its own
distinct query overstates how much actually varies in the codebase, and
buries the real question a migration or audit needs answered: *how many
genuinely different queries are there, and which files are just
variants of which others?*

`core_id` answers that by re-grouping the corpus: run `--extract-metadata`
over the whole tree, and every statement that shares a `core_id` with
another is the same core query. The point is a **short list of distinct
core queries**, not a long list of near-duplicates re-inflated back
toward the file count — which is exactly what happens if identity is too
strict (see "Condensed grouping" below).

## The fact set

Every statement is reduced to a set of canonical fact strings — the
*full* fact set — with six categories:

| Prefix | Example | Meaning |
|---|---|---|
| `TBL\|schema\|table` | `TBL\|(no-schema)\|TBACCT` | A real table referenced, alias resolved away |
| `JOINTYPE\|type=n` | `JOINTYPE\|LEFT=1` | Join-type multiset (`JOIN`/`INNER`/comma-join collapse to `INNER`; `LEFT`/`RIGHT`/`FULL`/`CROSS` stay distinct) |
| `REL\|op\|t1.c1\|t2.c2` | `REL\|=\|TBACCT.ACCT_ID\|TBCTRT.ACCT_ID` | A comparison joining two distinct tables (pair-sorted), from `ON` clauses and comma-join `WHERE` equalities alike |
| `PRED\|operand\|op` | `PRED\|TBSTAT.STAT_CD\|IN` | One `WHERE` filter predicate's operand signature + operator |
| `GROUPBY\|operand` | `GROUPBY\|TBACCT.ACCT_ID` | One `GROUP BY` item, same operand signature |
| `SHAPE\|BLOCKS=n` | `SHAPE\|BLOCKS=1` | Total query-block count (outer block + every CTE body/derived-table subquery) |

A `PRED`/`GROUPBY` operand is `TABLE.COL` for a resolvable qualified
column, the bare column name if unqualified, or `FN(...)` over a
function's column arguments (literal arguments are always dropped, so
`COUNT(*)` becomes `COUNT()` — only the function name and its column
inputs discriminate).

`SHAPE|BLOCKS` exists so a statement that only *wraps* another query —
`WITH cte AS (<q>) SELECT * FROM cte`, or `SELECT * FROM (<q>) x` — with
no join/predicate/grouping of its own doesn't collapse onto the bare `<q>`
it wraps just because it contributes no other fact of its own.

## Condensed grouping: what discriminates `core_id`

`core_id` is **not** a hash of the full fact set above. It's a hash of a
narrower subset that drops `PRED|` and `GROUPBY|` facts entirely — only
`TBL`/`JOINTYPE`/`REL`/`SHAPE` discriminate identity:

| Statement change | Changes `core_id`? | Why |
|---|---|---|
| Column alias / table alias renamed | No | Cosmetic, no fact category touches it |
| Extra SELECT-list column added | No | SELECT-list projection never contributes a fact |
| Derived-column arithmetic changed | No | Only the columns referenced matter (as `columns`, reporting-only) |
| Comma-join rewritten as ANSI `JOIN...ON` | No | Both resolve to the same `REL`/`JOINTYPE` facts |
| FROM-clause join order permuted | No | Facts are sets, not sequences |
| WHERE predicate added/changed/removed | **No** | `PRED\|` excluded on purpose — see below |
| GROUP BY item added/changed/removed | **No** | `GROUPBY\|` excluded on purpose — see below |
| HAVING / ORDER BY changed | No | Never contributes a fact at all |
| A table added or removed | Yes | New/missing `TBL\|` fact |
| Join type flipped (`LEFT`→`INNER`) | Yes | `JOINTYPE\|` multiset count shifts |
| Join topology changed (different tables linked) | Yes | `REL\|` fact set changes |
| Bare query vs. its own CTE/subquery/UNION wrapper | Yes | `SHAPE\|BLOCKS` differs |

The point of identity here is to collapse a corpus of thousands of files
down to a short list of *distinct core queries* — the same report re-run
with a narrower `WHERE` filter, or grouped by one extra column, is still
the same underlying query touching the same tables through the same
joins. Splitting it into its own `core_id` just re-inflates the "distinct
queries" list back toward the file count, defeating the point. Two
statements sharing a `core_id` can therefore still differ in their
filters/grouping — that's not lost information, it still lives in the
full fact set (`IdentityRow.fact_set`), which `--query-similarity` scores
over instead (see [query-similarity.md](query-similarity.md)) — it's just
not what *identity* discriminates on.

## Algorithm

1. Build the full fact set for a statement (`build_fact_set`).
2. Narrow it to just `TBL`/`JOINTYPE`/`REL`/`SHAPE` facts (`_facts_for_core_id`).
3. Sort the narrowed set, join with `\n`, SHA-256 it, and take the first
   16 hex characters (`core_id_for`) — deterministic and order-independent
   (a Python-native `hash()` would not be stable across processes, which
   matters once `--workers` scans files in parallel).

## Worked example: how `core_id` changes as the fact set changes

All values below are real output from this repo's own stress-corpus
fixtures (`tests/fixtures/20-37`), computed by actually running
`scan_file(..., ScanOptions(extract_query_identity=True))` — not
hand-simulated.

Base query (`20_query_identity_base.sql`): `TBACCT`/`TBCTRT`/`TBSTAT`/
`TBSAMPLE001` joined by two `INNER`s and one `LEFT OUTER`, filtered on
`STAT_CD IN (...)`, `CTRT_TYPE_CD <> '99'`, `OPEN_DT BETWEEN ...`, grouped
by five columns.

| Fixture | What changed vs. the base | `core_id` | Same as base? |
|---|---|---|---|
| `20_query_identity_base.sql` | — (base) | `88499a34355030b2` | — |
| `21_query_identity_alias_variant.sql` | Table aliases renamed | `88499a34355030b2` | **Yes** |
| `22_query_identity_extra_column.sql` | One extra SELECT-list column | `88499a34355030b2` | **Yes** |
| `23_query_identity_derived_column_variant.sql` | Derived-column (`CASE`) arithmetic changed | `88499a34355030b2` | **Yes** |
| `25_query_identity_predicate_variant.sql` | `WHERE`/`GROUP BY` predicates rewritten entirely (see below) | `88499a34355030b2` | **Yes** |
| `30_query_identity_comma_join_variant.sql` | One `JOIN...ON` rewritten as a comma-join + `WHERE` equality | `88499a34355030b2` | **Yes** |
| `31_query_identity_join_order_variant.sql` | FROM-clause join order permuted | `88499a34355030b2` | **Yes** |
| `24_query_near_miss_extra_join.sql` | One additional `LEFT OUTER JOIN TBCODE` added | `a421ecfeb3c7f8ac` | No |
| `32_query_near_miss_join_type_change.sql` | `TBSTAT`'s join flipped `LEFT OUTER`→`INNER` | `c776b2874f3f34d5` | No |
| `34_query_identity_core_b_base.sql` | Entirely different domain (HR tables, zero overlap) | `c818abc3f123eed0` | No |
| `27_query_distinct_single_table.sql` | Single table, no joins at all | `a19c38a2b3e49b39` | No |

`25_query_identity_predicate_variant.sql` is the sharpest illustration of
"condensed grouping": its `WHERE`/`GROUP BY` clauses are genuinely
different from the base's —

```sql
-- base (20):
WHERE C.STAT_CD IN ('01', '02')
  AND B.CTRT_TYPE_CD <> '99'
  AND A.OPEN_DT BETWEEN '20200101' AND '20261231'

-- variant (25):
WHERE C.STAT_CD = '01'
  AND A.CHANNEL_CD = 'WEB'
```

— yet it still lands on the exact same `core_id` as the base, because
every fact that differs between them is a `PRED|` fact, and `PRED|` never
reaches `core_id`. Its full `fact_set` is not identical to the base's
though (three `PRED` facts differ each way) — that's the difference
`--query-similarity` reports (Jaccard 0.667 between the two, see
[query-similarity.md](query-similarity.md)'s worked example).

By contrast, `24_query_near_miss_extra_join.sql` adds one extra table via
one extra `JOIN`. That's a genuine topology change — one new `TBL|` fact
(`TBL|(no-schema)|TBCODE`) and one new `REL|` fact — so it gets its own,
different `core_id`, even though eleven of its thirteen full facts are
identical to the base's.

## Supplementary fields (never read back into `core_id`)

Each identity row also carries fields that are useful for a human reading
`refs_query_identity.tsv`, but play no role in computing `core_id`:

- `columns` — every column the statement references, alias-resolved where
  possible. Not identity evidence: a `SELECT *` can't be resolved to
  columns without table layout information, so this can't be trusted the
  way `TBL`/`REL` facts can.
- `has_cte` / `has_subquery` / `has_union` — whether the statement's shape
  includes a `WITH` clause, a derived-table/scalar/`IN`/`EXISTS`
  subquery, or a `UNION`/`INTERSECT`/`EXCEPT`. `SHAPE|BLOCKS` is what
  actually keeps a wrapper statement from collapsing onto the bare query
  it wraps; these three just surface that shape in the TSV.
- `table_count` / `join_count` — counts derived from the narrowed,
  identity-relevant fact set, for a quick read of a cluster's size/shape
  without opening the full `fact_set`.

## Known limitations

- **Function fingerprints are name + column inputs only.** Two calls
  differing solely in literal arguments or argument order collapse onto
  the same signature.
- **A correlated subquery's outer-alias reference doesn't resolve**
  (scoping is per query block), so a `JOIN` and its correlated-`EXISTS`
  rewrite of the same intent deliberately get different `core_id`s — a
  known non-goal of a purely structural signature, not a bug.
- **`has_subquery` can under-report** on a statement that doesn't parse as
  one clean tree (e.g. a reserved-keyword-colliding alias elsewhere in the
  same statement) — `has_cte`/`has_union` don't share this weakness,
  since they're read straight off the token stream instead of the parse
  tree.

## Relationship to `--query-similarity`

`core_id` and `--query-similarity` are two resolutions of the same
underlying data, deliberately kept separate:

- `core_id` groups statements into a **short list of distinct core
  queries** — a hard equivalence class, computed over a narrowed fact set
  that excludes `PRED`/`GROUPBY` on purpose.
- `--query-similarity` scores statements that **don't** share a `core_id`
  against each other, over their **full** fact set (`PRED`/`GROUPBY`
  included) — surfacing near-misses at a finer resolution than identity
  does, without re-inflating the distinct-core-query count to do it.

See [query-similarity.md](query-similarity.md) for that computation in
full, with the same fixtures' actual similarity scores worked through.
