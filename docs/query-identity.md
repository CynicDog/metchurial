# Query Identity (`core_id`)

`--extract-metadata` assigns every SQL statement a `core_id`: a short,
deterministic hash of that statement's structural signature. Statements
that are the same underlying query — differing only in things like
aliasing, which columns get selected, or how a derived column is
calculated — collapse onto the same `core_id`. Statements that touch
different tables, or join them differently, get different ones.

Whether `WHERE`/`GROUP BY` clauses also discriminate identity is
configurable via `--identity-granularity` (four tiers, see "Condensed
grouping" below) — `core_id` is hashed from a *subset* of the six fact
categories a statement is reduced to, and which subset is a per-run
choice, not a fixed rule. The default tier (`structure`) excludes
predicates and grouping, reproducing this feature's original behavior
before granularity became configurable.

This document covers *why* `core_id` exists, exactly what it hashes, and
a worked example — an illustrative query run through the actual
implementation, with its real computed `core_id` values at the default
`structure` tier — showing how a change to a query's SQL does or doesn't
move its `core_id`. See [query-similarity.md](query-similarity.md) for the
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

## The full fact set

Every statement is reduced to a set of canonical fact strings — the
*full* fact set — with six categories. **Not all six necessarily feed
into `core_id`** — this table is the complete vocabulary a statement is
reduced to; the next section ("Condensed grouping") narrows it down to
whichever categories the chosen `--identity-granularity` tier includes
(four are always in; `PRED`/`GROUPBY` only join in at the stricter
tiers):

| Prefix | Example | Meaning |
|---|---|---|
| `TBL\|schema\|table` | `TBL\|(no-schema)\|TBACCT` | **Every** real table referenced, alias resolved away — one fact per table, whether or not it's joined to anything |
| `JOINTYPE\|type=n` | `JOINTYPE\|LEFT=1` | Join-type multiset (`JOIN`/`INNER`/comma-join collapse to `INNER`; `LEFT`/`RIGHT`/`FULL`/`CROSS` stay distinct) |
| `REL\|op\|t1.c1\|t2.c2` | `REL\|=\|TBACCT.ACCT_ID\|TBCTRT.ACCT_ID` | A comparison *connecting* two distinct tables (pair-sorted), from `ON` clauses and comma-join `WHERE` equalities alike — a separate signal from `TBL` about *how* two already-recorded tables relate, not a substitute for recording them |
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
narrower subset selected by `--identity-granularity`, one of four tiers,
loosest to strictest:

| `--identity-granularity` | Fact categories included | Notes |
|---|---|---|
| `table` | `TBL` | Loosest — any two statements touching the same table *set* share a `core_id`, regardless of how (or whether) they join those tables |
| `structure` (**default**) | `TBL`, `JOINTYPE`, `REL`, `SHAPE` | Original, still-default behavior — join topology/type and query shape all discriminate, filters/grouping don't |
| `filtered` | `structure` + `PRED` | WHERE predicates now also discriminate |
| `strict` | `filtered` + `GROUPBY` | Strictest — the full fact set; two statements share a `core_id` only if every fact matches |

At the **default `structure` tier**:

| Statement change | Changes `core_id`? | Why |
|---|---|---|
| Column alias / table alias renamed | No | Cosmetic, no fact category touches it |
| Extra SELECT-list column added | No | SELECT-list projection never contributes a fact |
| Derived-column arithmetic changed | No | Only the columns referenced matter (as `columns`, reporting-only) |
| Comma-join rewritten as ANSI `JOIN...ON` | No | Both resolve to the same `REL`/`JOINTYPE` facts |
| FROM-clause join order permuted | No | Facts are sets, not sequences |
| WHERE predicate added/changed/removed | **No** | `PRED\|` excluded at this tier — included at `filtered`/`strict` |
| GROUP BY item added/changed/removed | **No** | `GROUPBY\|` excluded at this tier — included at `strict` |
| HAVING / ORDER BY changed | No | Never contributes a fact at all, at any tier |
| A table added or removed | Yes | New/missing `TBL\|` fact — changes `core_id` at every tier, including `table` |
| Join type flipped (`LEFT`→`INNER`) | Yes | `JOINTYPE\|` multiset count shifts — no effect at the `table` tier |
| Join topology changed (different tables linked) | Yes | `REL\|` fact set changes — no effect at the `table` tier |
| Bare query vs. its own CTE/subquery/UNION wrapper | Yes | `SHAPE\|BLOCKS` differs — no effect at the `table` tier |

The point of identity is to collapse a corpus of thousands of files down
to a short list of *distinct core queries*. At `structure`, the same
report re-run with a narrower `WHERE` filter, or grouped by one extra
column, is still the same underlying query touching the same tables
through the same joins — splitting it into its own `core_id` just
re-inflates the "distinct queries" list back toward the file count,
defeating the point. `table` collapses further still (join topology stops
mattering too) for a coarser "which tables does this codebase actually
touch, together" pass; `filtered`/`strict` go the other way for callers
who want a stricter notion of "the same query" that also cares about which
rows get selected or how they're grouped.

Two statements sharing a `core_id` at a given tier can still differ in
facts a stricter tier would have split them on — that's not lost
information, it still lives in the full fact set (`IdentityRow.fact_set`),
which `--query-similarity` scores over *regardless of granularity* (see
[query-similarity.md](query-similarity.md)) — it's just not always what
*identity* discriminates on. `--identity-granularity` requires
`--extract-metadata` unless left at its default; passing a non-default
value without it is a usage error, since it has nothing to affect.

The five supplementary `IdentityRow` fields (`table_count`, `join_count`,
`tables`, `join_types`, `relations`) are read from the **full** fact set,
not the granularity-narrowed one, so they stay meaningful at every tier —
at `table`, for instance, `join_count`/`join_types`/`relations` still
report the statement's real joins even though joins don't discriminate its
`core_id`.

## Algorithm

1. Build the full fact set for a statement (`build_fact_set`).
2. Narrow it to the categories the chosen `--identity-granularity` tier
   includes (`_facts_for_granularity`).
3. Sort the narrowed set, join with `\n`, SHA-256 it, and take the first
   16 hex characters (`core_id_for`) — deterministic and order-independent
   (a Python-native `hash()` would not be stable across processes, which
   matters once `--workers` scans files in parallel).

## Worked example: how `core_id` changes as the fact set changes

The base query below, and every variant of it in this section, are real
SQL run through the actual implementation
(`scan_file(..., ScanOptions(extract_query_identity=True))`, i.e. the
default `structure` granularity tier) — the `core_id` values shown are
genuine computed output, not invented. `ACCT`/`CTRT`/`STAT`/`SAMPLE` are
placeholder table names (account/contract/status/sample-attribute); swap
in your own schema mentally, the mechanics don't change.

**Base query:**

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

This resolves to `core_id 88499a34355030b2` — 4 `TBL`, 2 `JOINTYPE`, 3
`REL`, 3 `PRED`, 1 `SHAPE` fact (13 facts total).

| Variant | What changed vs. the base | `core_id` | Same as base? |
|---|---|---|---|
| *(base, above)* | — | `88499a34355030b2` | — |
| Aliases renamed (`A`→`ACC`, `B`→`CON`, ...) | Cosmetic only | `88499a34355030b2` | **Yes** |
| One extra SELECT-list column added | SELECT-list projection never contributes a fact | `88499a34355030b2` | **Yes** |
| `CASE` arithmetic recalculated differently | Only referenced columns matter, not the formula | `88499a34355030b2` | **Yes** |
| `WHERE`/`GROUP BY` rewritten entirely (see below) | All differences are `PRED\|`/`GROUPBY\|` facts | `88499a34355030b2` | **Yes** |
| One `JOIN...ON` rewritten as a comma-join + `WHERE` equality | Resolves to the same `REL`/`JOINTYPE` facts | `88499a34355030b2` | **Yes** |
| FROM-clause join order permuted | Facts are sets, not sequences | `88499a34355030b2` | **Yes** |
| One additional table joined in (e.g. `LEFT OUTER JOIN TBCODE E ON B.CTRT_TYPE_CD = E.CODE_CD`) | New `TBL\|`/`REL\|` fact — genuine topology change | `a421ecfeb3c7f8ac` | No |
| `TBSTAT`'s join flipped `LEFT OUTER`→`INNER` | `JOINTYPE\|` multiset count shifts | `c776b2874f3f34d5` | No |
| Entirely different domain/tables (zero table overlap) | Disjoint `TBL`/`REL` facts | `c818abc3f123eed0` | No |
| Single table only, no joins at all | Missing `REL`/`JOINTYPE` facts entirely | `a19c38a2b3e49b39` | No |

The "`WHERE`/`GROUP BY` rewritten entirely" row is the sharpest
illustration of "condensed grouping" — its filter is genuinely different
from the base's, not just reformatted:

```sql
-- base:
WHERE C.STAT_CD IN ('01', '02')
  AND B.CTRT_TYPE_CD <> '99'
  AND A.OPEN_DT BETWEEN '20200101' AND '20261231'

-- variant:
WHERE C.STAT_CD = '01'
  AND A.CHANNEL_CD = 'WEB'
```

— yet it still lands on the exact same `core_id` as the base, because
every fact that differs between them is a `PRED|` fact, and `PRED|` never
reaches `core_id`. Its full `fact_set` is not identical to the base's
though (three `PRED` facts differ each way) — that's the difference
`--query-similarity` reports (Jaccard 0.667 between the two, see
[query-similarity.md](query-similarity.md)'s worked example).

By contrast, the "one additional table joined in" row adds one extra
table via one extra `JOIN`. That's a genuine topology change — one new
`TBL|` fact and one new `REL|` fact — so it gets its own, different
`core_id`, even though eleven of its thirteen full facts are identical to
the base's.

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
- `table_count` / `join_count` — counts derived from the statement's
  **full** fact set (not the granularity-narrowed one `core_id` hashes),
  for a quick read of a cluster's size/shape without opening `fact_set`
  itself. Deliberately independent of `--identity-granularity`, so they
  stay accurate even at the `table` tier, where joins don't discriminate
  `core_id` but still happened.

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
  whose breadth is a per-run choice (`--identity-granularity`), not fixed.
- `--query-similarity` scores statements that **don't** share a `core_id`
  against each other, over their **full** fact set (`PRED`/`GROUPBY`
  included, regardless of which `--identity-granularity` tier the run
  used) — surfacing near-misses at a finer resolution than identity
  does, without re-inflating the distinct-core-query count to do it.

See [query-similarity.md](query-similarity.md) for that computation in
full, worked through against the same example query above.
