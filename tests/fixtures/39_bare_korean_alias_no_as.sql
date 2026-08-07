-- ==========================================================================
-- 39_bare_korean_alias_no_as.sql
-- What it does: Column aliases written in bare unquoted Korean with no AS
--   keyword: they must lex as identifiers rather than as lexer errors that
--   would trip the bad-file ratio gate.
-- Modules: detect/bad_file_check.py, references/table_scan.py,
--   references/reference_visitor.py
-- ==========================================================================

SELECT a.col1 가나다
     , a.col2 라마바
-- , a.col3 사아자차
-- , SUM(a.col4) 카타파하
     , a.col5 다라마바
     , COALESCE(a.자차카타)
FROM tbl_a a, tbl_a b
WHERE a.a = b.b
ORDER BY 가나다, 다라마바
