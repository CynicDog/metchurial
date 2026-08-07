-- ==========================================================================
-- 05_korean_names.sql
-- What it does: Korean name-shaped string literals in a SELECT list:
--   untriaged name candidates for strings.txt and the known-name pass, not
--   predicate findings.
-- Modules: engine.py, report.py, io_utils.py
-- ==========================================================================

SELECT '홍길동' AS DUMMY_NAME FROM SYSIBM.SYSDUMMY1;
SELECT '강남구' AS DISTRICT FROM SYSIBM.SYSDUMMY1;
