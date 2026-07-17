-- Deliberately malformed/non-SQL content for the bad_files.txt workflow
-- (src/detect/bad_file_check.py): bracketed section markers, missing
-- semicolons, numbered prose headers instead of real comments, a
-- decorative divider line, and a truncated CTE -- all sitting directly
-- in the file body rather than behind '--'/'/* */'.

<<목표KPI>>
SELECT SUM(KPI_METRICS)
FROM TAB1
WHERE YEAR_MONTH = '202608'

========
(실적확인)

1) 인원기준
SELECT AMT
FROM EMPLOYEE_PERFORMANCE
WHERE EMPLOYEE_NO = '22222'

2) 정산
SELECT SUM(AMT)
FROM EMPLOYEE_CLOSE
WHERE ABC = 'aaa'

<<조직>>;
with aaa as (
    ..
)
