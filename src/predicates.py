# -*- coding: utf-8 -*-
"""Shared classification of the grammar's flat `predicate` rule.

The vendored Db2 grammar merges every predicate alternative (comparisons,
BETWEEN, LIKE, IS NULL, IN, EXISTS, cursor states, ...) into one rule with
a single generated ``PredicateContext`` class -- there are no
per-alternative subclasses to dispatch on. Which alternative actually
matched is recoverable only by probing which optional accessors are
populated. This module centralizes that probing so every consumer
(extraction, relations, query identity, function/operator usage) shares
one classifier instead of re-deriving the alternative shape.
"""

COMPARISON_OPS = frozenset(("=", "<>", "<", ">", "<=", ">="))


def classify_predicate(ctx):
    """Return the operator name for a supported predicate alternative.

    Supported alternatives and their return values:

    * binary comparison -> the operator text (``=``, ``<>``, ``<``, ``>``,
      ``<=``, ``>=``); quantified comparisons (``= ANY (...)``) are excluded
    * range test -> ``BETWEEN`` / ``NOT BETWEEN``
    * pattern match -> ``LIKE`` / ``NOT LIKE``
    * null test -> ``IS NULL`` / ``IS NOT NULL``
    * membership test -> ``IN`` / ``NOT IN``; the ``IN`` token is also used
      by the ``IS [NOT] DISTINCT FROM``, cursor ``IN (FOUND | OPEN)``, and
      dynamic-type-check alternatives, which are excluded by their own
      accessors (``DISTINCT``/``FOUND``/``OPEN``/``cursor_variable_name``)

    Every other alternative (EXISTS, OVERLAPS, ``IS [NOT] (TRUE | FALSE)``,
    ...) returns ``None``.
    """
    exprs = ctx.expression()
    op_ctx = ctx.comparison_operator()
    if op_ctx is not None and len(exprs) == 2 and ctx.some_any_all() is None:
        return op_ctx.getText()
    if ctx.BETWEEN() is not None:
        return "NOT BETWEEN" if ctx.NOT() is not None else "BETWEEN"
    if ctx.LIKE() is not None:
        return "NOT LIKE" if ctx.NOT() is not None else "LIKE"
    if ctx.NULL_() is not None:
        return "IS NOT NULL" if ctx.NOT() is not None else "IS NULL"
    if (ctx.IN() is not None and ctx.DISTINCT() is None
            and ctx.FOUND() is None and ctx.OPEN() is None
            and ctx.cursor_variable_name() is None):
        return "NOT IN" if ctx.NOT() is not None else "IN"
    return None


def subject_expression(ctx, op):
    """Return the tested-value (column-side) ``ExpressionContext`` of a
    single-subject predicate.

    ``op`` is a ``classify_predicate`` result. BETWEEN and IS [NOT] NULL
    expose the subject as the first generic ``expression()`` child; LIKE
    and IN expose it through the grammar's labeled fields (``me``/``e``).
    Binary comparisons have two equal operands rather than one subject, so
    they -- and unsupported alternatives -- return ``None``.
    """
    if op in ("BETWEEN", "NOT BETWEEN", "IS NULL", "IS NOT NULL"):
        return ctx.expression()[0]
    if op in ("LIKE", "NOT LIKE"):
        return ctx.me
    if op in ("IN", "NOT IN"):
        return ctx.e
    return None
