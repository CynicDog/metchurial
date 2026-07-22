# Query Similarity (`--query-similarity`)

`--query-similarity` scores statements that **don't** share a `core_id`
against each other, so a corpus scan can still surface *near-misses* —
two statements that are clearly related (same base tables, one added
join, a flipped join type) even though they landed on different
`core_id`s. It requires `--extract-metadata` and is itself opt-in, since
it's the one O(n²) pass in the whole tool.

This document covers what similarity is computed over, the exact scoring
algorithm, and worked examples (real, computed values from this repo's
own test fixtures) showing how the score moves as the underlying SQL
changes. Read [query-identity.md](query-identity.md) first if you haven't
— this feature is best understood as identity's finer-grained
complement, not a replacement for it.

## Purpose

`core_id` (see [query-identity.md](query-identity.md)) deliberately
ignores `WHERE`/`GROUP BY` differences so a corpus doesn't re-inflate back
toward one `core_id` per file. But that means two statements that touch
the *same* tables through *almost* the same joins — one extra `JOIN`, one
join type flipped from `LEFT` to `INNER` — get different, unrelated-looking
`core_id`s, with nothing in `refs_query_identity.tsv` alone connecting
them. A reviewer scanning core queries has no way to tell "these two
`core_id`s are basically the same query, edited" from "these two
`core_id`s are unrelated queries that happen to both touch four tables."

`--query-similarity` closes that gap: it scores every pair of *distinct*
`core_id`s against each other and reports the ones that score above a
threshold, along with a human-readable list of exactly which facts differ
— so a reviewer can see not just *that* two core queries are related, but
*why*, and *how much*.

## What it's computed over

Similarity is scored over each distinct `core_id`'s **full** fact set —
`IdentityRow.fact_set` — which is the same six categories `core_id` itself
is built from (`TBL`/`JOINTYPE`/`REL`/`PRED`/`GROUPBY`/`SHAPE`; see
[query-identity.md](query-identity.md#the-fact-set)), but *without*
`core_id`'s own `PRED`/`GROUPBY` exclusion. This is deliberate: identity's
whole point is to ignore filter/grouping differences so the corpus
collapses to a short list; similarity's whole point is the opposite — to
surface exactly those finer-grained differences once two statements have
already failed to collapse into the same `core_id` on tables/joins alone.

One consequence worth being explicit about: **two statements that share a
`core_id` are never scored against each other**, even though their full
fact sets can differ (that's exactly the `25_query_identity_predicate_
variant.sql` case in query-identity.md's worked example — same `core_id`
as the base, different `fact_set`). `compute_similarity` takes one
representative fact set per distinct `core_id` before scoring any pairs,
so same-`core_id` statements collapse into a single representative first
and are structurally incapable of being compared to each other by this
pass. Similarity only ever answers "how related are these two *different*
core queries", never "how related are two variants that already
collapsed into the same one."

## Algorithm

1. **Take one representative fact set per distinct `core_id`** across
   every identity row gathered so far (`compute_similarity` runs once,
   corpus-wide, after a full scan — not per file).
2. **Score every pair of distinct `core_id`s** with Jaccard similarity:

   ```
   similarity(A, B) = |factsA ∩ factsB| / |factsA ∪ factsB|
   ```

3. **Keep pairs scoring at or above `threshold`** (CLI default `0.5`),
   sorted by similarity descending.
4. Each kept pair also reports `shared_facts` (the intersection size) and
   `only_in_a`/`only_in_b` — the human-readable symmetric difference, so a
   reader sees *which* facts actually differ, not just the score.

This is `O(unique_core_ids²)` — fine for thousands of distinct queries,
slow for tens of thousands, which is why it's opt-in rather than bundled
into `--extract-metadata` itself.

## Worked example: how the score moves as the fact set changes

All numbers below come from actually running `compute_similarity`/
`_jaccard` over this repo's own stress-corpus fixtures
(`tests/fixtures/20-37`) — not hand-computed.

Base query (`20_query_identity_base.sql`, `core_id` `88499a34355030b2`)
has 13 full facts: 4 `TBL`, 2 `JOINTYPE`, 3 `REL`, 3 `PRED`, 1 `SHAPE`.

| Compared against | Its `core_id` | What changed | Shared facts | Similarity | Read as |
|---|---|---|---|---|---|
| `25_query_identity_predicate_variant.sql` | `88499a34355030b2` (**same as base**) | `WHERE`/`GROUP BY` rewritten | 10 / 13 ∪ 12 = 15 | 0.667 | Same core query (never actually scored by `--query-similarity` — see above; shown here only to demonstrate that `fact_set` still differs even on a shared `core_id`) |
| `32_query_near_miss_join_type_change.sql` | `c776b2874f3f34d5` | One join `LEFT`→`INNER` | 11 / 14 | **0.786** | Highest score among the distinct-`core_id` cases — smallest possible structural edit |
| `24_query_near_miss_extra_join.sql` | `a421ecfeb3c7f8ac` | One extra `JOIN TBCODE` added | 12 / 16 | 0.750 | Clearly related — same base + one added edge |
| `34_query_identity_core_b_base.sql` | `c818abc3f123eed0` | Unrelated domain (HR tables) | 2 / 22 | 0.091 | Below threshold — correctly scores as unrelated |

The ordering makes the intuition concrete: **flipping one join's type is
a smaller structural edit than adding a whole new joined table**, and
`--query-similarity` reflects that directly — 0.786 vs. 0.750 — without
either statement sharing the base's `core_id`.

### Reading `only_in_a` / `only_in_b`

For the join-type-flip pair above (base vs.
`32_query_near_miss_join_type_change.sql`):

| Column | Value |
|---|---|
| `only_in_a` (in base, not in the variant) | `join-type INNER=2`, `join-type LEFT=1` |
| `only_in_b` (in the variant, not in base) | `join-type INNER=3` |

Every `TBL`/`REL`/`PRED` fact is identical between the two — the *entire*
symmetric difference is the `JOINTYPE` multiset shifting from
`{INNER: 2, LEFT: 1}` to `{INNER: 3}`, which is exactly the one-keyword
edit (`LEFT OUTER JOIN` → `INNER JOIN`) the fixture makes. A reader
scanning `refs_query_similarity.tsv` sees this and immediately knows *what
changed*, not just that something did.

For the near-miss with an unrelated domain (base vs.
`34_query_identity_core_b_base.sql`), `only_in_a`/`only_in_b` list every
single fact on each side — all 11 base facts and all 9 of the other's,
zero overlap beyond `SHAPE|BLOCKS=1` and one shared `JOINTYPE` count. That
near-total symmetric difference is what a 0.091 score looks like in
practice: two statements with almost nothing in common beyond both being
one-block SELECTs with a couple of joins.

## Output: `refs_query_similarity.tsv`

One row per scored pair (only pairs at or above `threshold`):

| Column | Meaning |
|---|---|
| `core_id_a` / `core_id_b` | The two distinct core queries being compared |
| `similarity` | Jaccard score, rounded to 3 decimals |
| `shared_facts` | Size of the intersection |
| `only_in_a` / `only_in_b` | Human-readable symmetric difference (sorted) |

Pairs are sorted by `similarity` descending, so the most-related
core-query pairs are at the top.

## CLI usage

```
metchurial --extract-metadata --query-similarity <path>
```

`--query-similarity` requires `--extract-metadata` (it has nothing to
score without `refs_query_identity.tsv`'s identity rows) and is off by
default — see [query-identity.md](query-identity.md) for what feeds into
it and why the two features are kept as separate opt-in passes rather
than one combined one.
