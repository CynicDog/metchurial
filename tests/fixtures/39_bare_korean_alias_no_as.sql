SELECT a.col1 가나다
     , a.col2 라마바
-- , a.col3 사아자차
-- , SUM(a.col4) 카타파하
     , a.col5 다라마바
     , COALESCE(a.자차카타)
FROM tbl_a a, tbl_a b
WHERE a.a = b.b
ORDER BY 가나다, 다라마바
