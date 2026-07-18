#!/usr/bin/env bash
# Dev-only: regenerates the Python3 ANTLR lexer/parser/visitor from the
# vendored Db2 grammar. Requires Java + antlr4-tools (see pyproject.toml's
# [dependency-groups] dev group -- `uv sync` installs it). NOT run in the
# restricted target environment -- src/metchurial/_generated/ is committed so that
# environment never needs Java or ANTLR.
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
GRAMMAR_DIR="$ROOT/vendor/grammars-v4"
OUT_DIR="$ROOT/src/metchurial/_generated"

rm -rf "$OUT_DIR"
mkdir -p "$OUT_DIR"

# Db2Parser.g4 is a separate parser grammar (options { tokenVocab=Db2Lexer; }),
# not a combined grammar -- ANTLR requires Db2Lexer.tokens to already exist
# before it can resolve the parser's string-literal token references (e.g.
# '(' -> LEFT_RND_BKT), so the lexer must be generated first, then the
# parser pointed at that output via -lib. Generating both in one pass
# fails with "cannot create implicit token for string literal in
# non-combined grammar" even though every literal the parser uses is a
# real named token in the lexer.
antlr4 -Dlanguage=Python3 -o "$OUT_DIR" "$GRAMMAR_DIR/Db2Lexer.g4"
antlr4 -Dlanguage=Python3 -visitor -no-listener -lib "$OUT_DIR" -o "$OUT_DIR" "$GRAMMAR_DIR/Db2Parser.g4"

touch "$OUT_DIR/__init__.py"

echo "Generated parser written to $OUT_DIR"
