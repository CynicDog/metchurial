-- 기준값을 변수로 선언
WITH CONFIG AS (
    SELECT '202606' AS 종료, '201907' AS 시작
    FROM SYSIBM.SYSDUMMY1
),
AUX AS (
    SELECT COL_A, ID1, SEQ1, TRT_ID, TYPE_CD, AMT1
    FROM T_REF  -- 보조 원본에서 조회
)
SELECT
    구분1,
    날짜1,
    날짜2,
    INT((LEFT(C.종료,4) - LEFT(날짜1,4))
        + (CASE WHEN SUBSTR(C.종료,5,2) < SUBSTR(날짜1,5,2) THEN 1 ELSE 0 END)) AS DUR_A,
    INT((LEFT(날짜2,4) - LEFT(날짜1,4))
        + (CASE WHEN SUBSTR(C.종료,5,2) < SUBSTR(날짜2,5,2) THEN 1 ELSE 0 END)
        - (CASE WHEN SUBSTR(C.종료,5,2) < SUBSTR(날짜1,5,2) THEN 1 ELSE 0 END)) AS DUR_B,
    CASE
        WHEN T_OVR.GRP_ID IS NOT NULL THEN T_OVR.GRP_ID
        ELSE
            CASE
                WHEN T_MAP.GRP_ID IS NULL THEN DFT.GRP_ID
                ELSE T_MAP.GRP_ID
            END
    END AS GRP_ID,
    SUM(금액1) AS 금액1,
    SUM(금액2) AS 금액2,
    SUM(금액3) AS 금액3,
    SUM(금액1 + 금액2 + 금액3) AS 합계금액,
    COUNT(DISTINCT KEY_) AS CNT
FROM
(
    -- 값1
    SELECT
        CASE
            WHEN LEFT(CODE_DTL,2) IN ('AA','AD') AND AMT_TYPE NOT IN ('5121','5111','5150') THEN '000100' -- 유형 A
            WHEN LEFT(CODE_DTL,2) IN ('DB','FA','DD') OR AMT_TYPE IN ('5121','5111','5150') THEN '000200' -- 유형 B
            WHEN LEFT(CODE_DTL,2) IN ('BB') THEN '000300'
            WHEN LEFT(CODE_DTL,2) IN ('CC') THEN '000400'
            ELSE GRP_CD
        END AS 구분1,
        CASE
            WHEN GRP_CD = '000200' OR AMT_TYPE IN ('5121','5111','5150') OR ISNULL(AUX.TYPE_CD, A.TYPE_CD) = 2
                THEN LEFT(DT1,6)  -- 조건 충족 시 기준일자 A
            ELSE LEFT(DT2,6)  -- 그 외 기준일자 B
        END AS 날짜1,
        LEFT(COL_B,6) AS 날짜2,
        SRC_AMT_A AS 금액1,
        0 AS 금액2,
        0 AS 금액3,
        A.TRT_ID || A.SEQ1 AS KEY_
    FROM T1 A
    LEFT JOIN AUX
        ON A.TRT_ID = AUX.TRT_ID
        AND A.SEQ1 = AUX.SEQ1
        AND A.COL_A = AUX.COL_A
        AND A.ID1 = AUX.ID1
    , CONFIG C
    WHERE (A.COL_A BETWEEN C.시작 AND C.종료 AND FLAG_A = '1')
       OR (A.COL_A = C.종료 AND FLAG_A = '0')

    UNION ALL

    -- 값2
    SELECT
        GRP_CD AS 구분1,
        CASE
            WHEN GRP_CD = '000200' OR AMT_TYPE IN ('5121','5111','5150') OR ISNULL(AUX.TYPE_CD, A.TYPE_CD) = 2
                THEN LEFT(DT1,6)  -- 조건 충족 시 기준일자 A
            ELSE LEFT(DT2,6)  -- 그 외 기준일자 B
        END AS 날짜1,
        LEFT(COL_B,6) AS 날짜2,
        0 AS 금액1,
        SRC_AMT_B AS 금액2,
        0 AS 금액3,
        A.TRT_ID || A.SEQ1 || 'A' AS KEY_
    FROM T2 A
    LEFT JOIN AUX
        ON A.TRT_ID = AUX.TRT_ID
        AND A.SEQ1 = AUX.SEQ1
    , CONFIG C
    WHERE LEFT(A.COL_B,6) = C.종료
        AND CASE
            WHEN GRP_CD = '000200' OR AMT_TYPE IN ('5121','5111','5150') OR ISNULL(AUX.TYPE_CD, A.TYPE_CD) = 2
                THEN LEFT(DT1,6)
            ELSE LEFT(DT2,6)
        END BETWEEN C.시작 AND C.종료

    UNION ALL

    -- 값3
    SELECT
        GRP_CD AS 구분1,
        CASE
            WHEN GRP_CD = '000200' OR AMT_TYPE IN ('5121','5111','5150') OR ISNULL(AUX.TYPE_CD, A.TYPE_CD) = 2
                THEN LEFT(DT1,6)  -- 조건 충족 시 기준일자 A
            ELSE LEFT(DT2,6)  -- 그 외 기준일자 B
        END AS 날짜1,
        LEFT(A.COL_B,6) AS 날짜2,
        0 AS 금액1,
        0 AS 금액2,
        SRC_AMT_C AS 금액3,
        A.TRT_ID AS KEY_
    FROM T1 A
    LEFT JOIN AUX
        ON A.ID1 = AUX.ID1
        AND A.SEQ1 = AUX.SEQ1
    , CONFIG C
    WHERE SRC_AMT_C <> 0
        AND CODE1 IN (SELECT CODE1 FROM T_CODE WHERE CODE2 = '700' AND CODE3 NOT IN ('XXX'))
        AND CASE
            WHEN A.GRP_CD = '000200' OR AMT_TYPE IN ('5121','5111','5150') OR ISNULL(AUX.TYPE_CD, A.TYPE_CD) = 2
                THEN LEFT(A.DT1,6)
            ELSE LEFT(A.DT2,6)
        END BETWEEN C.시작 AND C.종료
        AND A.COL_A BETWEEN '201912' AND '202012'
) AS UNIFIED_DATA
, CONFIG C
LEFT JOIN T_MAP ON UNIFIED_DATA.ID1 = T_MAP.ID1
LEFT JOIN (
    SELECT DISTINCT RCODE1
    FROM T_REF, CONFIG C2
    WHERE COL_A BETWEEN C2.시작 AND C2.종료 AND FLAG1 = 1
) AS PAA ON UNIFIED_DATA.RCODE1 = PAA.RCODE1
LEFT JOIN (
    SELECT ID1, RCODE1,
        MIN(CASE
            WHEN DT3 BETWEEN '20211200' AND '20211299' THEN '8001'
            WHEN DT3 BETWEEN '20220100' AND '20221299' THEN '8002'
            WHEN DT3 BETWEEN '20230100' AND '20231299' THEN '8003'
            WHEN DT3 BETWEEN '20240100' AND '20240399' THEN '8004'
            WHEN DT3 BETWEEN '20240400' AND '20240699' THEN '8005'
            WHEN DT3 BETWEEN '20240700' AND '20240999' THEN '8006'
            WHEN DT3 BETWEEN '20241000' AND '20241299' THEN '8007'
            WHEN DT3 BETWEEN '20250100' AND '20250399' THEN '8008'
            WHEN DT3 BETWEEN '20250400' AND '20250699' THEN '8009'
            WHEN DT3 BETWEEN '20250700' AND '20250999' THEN '8010'
            WHEN DT3 BETWEEN '20251000' AND '20251299' THEN '8011'
            WHEN DT3 BETWEEN '20260100' AND '20260399' THEN '8012'
        END) AS TERM_CD
    FROM T_HIST
    GROUP BY ID1, RCODE1
) AS TEMP ON UNIFIED_DATA.ID1 = TEMP.ID1 AND UNIFIED_DATA.RCODE1 = TEMP.RCODE1
GROUP BY 구분1, 날짜1, 날짜2, GRP_ID;
