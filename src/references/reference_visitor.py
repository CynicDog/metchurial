# -*- coding: utf-8 -*-
"""--extract-metadata's column-level extraction visitor -- walks *every*
column reference in a chunk (not just ones compared to a literal, unlike
extractor_visitor.ExtractorVisitor's sensitive-column comparison detection
scope) and resolves each one
to its owning schema.table via table_scan.py's per-chunk QueryBlock alias
maps. A separate class from ExtractorVisitor because the traversal shape
is genuinely different: unconditional on every column_name/field_reference
node, not gated behind a comparison/predicate shape.

Db2Parser's `column_name` rule is always a bare, unqualified identifier;
a table/alias-qualified reference (`a.ACCT_ID`) instead parses through the
*separate* `field_reference` rule (`row_variable_name '.' field_name`) --
see table_scan.py's module docstring for why alias resolution can't be
done structurally and needs table_scan.resolve_qualifier's character-
offset-scoped lookup instead.
"""

from Db2Parser import Db2Parser
from Db2ParserVisitor import Db2ParserVisitor

from src.references import table_scan


class ReferenceVisitor(Db2ParserVisitor):

    def __init__(self, query_blocks, sink):
        """query_blocks: list[table_scan.QueryBlock] for the chunk this
        visitor's trees belong to -- computed by
        table_scan.scan_query_blocks *before* this visitor is
        constructed (see scan.py's pre_chunk_hook, which builds one
        ReferenceVisitor per chunk closing over that chunk's own blocks).
        sink: callable(schema, table, column, line) invoked once per
        syntactic column-reference occurrence -- not pre-deduplicated;
        dedup happens at the report layer (report.write_refs_tsv), same
        division of labor as ExtractorVisitor's sink convention."""
        self.query_blocks = query_blocks
        self.sink = sink

    def visitColumn_name(self, ctx: Db2Parser.Column_nameContext):
        name = ctx.id_().getText().upper()
        self.sink(table_scan.PLACEHOLDER_SCHEMA, table_scan.PLACEHOLDER_TABLE,
                 name, ctx.start.line)
        return self.visitChildren(ctx)

    def visitField_reference(self, ctx: Db2Parser.Field_referenceContext):
        qualifier = ctx.row_variable_name().getText().upper()
        column = ctx.field_name().getText().upper()
        schema, table = table_scan.resolve_qualifier(
            self.query_blocks, ctx.start.start, qualifier)
        self.sink(schema, table, column, ctx.start.line)
        return self.visitChildren(ctx)
