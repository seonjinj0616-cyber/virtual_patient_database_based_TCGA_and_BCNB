# TCGA ① (수술 후) 가상환자 세트 — 생성 보고

mini 커밋: `150c938` · 실행: `python -m vh.build`

## 인원

| 항목 | 수 |
|---|---|
| 세트 (관문 통과) | 707 |
| 뺀 환자: S-02 | 8 |
| 뺀 환자: S-03 | 9 |
| 뺀 환자: S-04 | 80 |
| 뺀 환자: S-07 | 25 |
| 뺀 환자: S-08 | 7 |
| 뺀 환자: S-09 | 2 |
| 넘길 목록 (실제 값 원인) | 0 |

아형 (규칙 판정): HR+/HER2- 469, HER2+ 126, TNBC 112

## 칸 출처 (present 칸 수)

| origin | 규칙 | 칸 수 |
|---|---|---|
| derived | D-01 | 707 |
| derived | D-03 | 707 |
| derived | D-05 | 975 |
| derived | D-06 | 97 |
| derived | D-08 | 286 |
| real | D-09 | 137 |
| real | M-01 | 11396 |
| synthetic | Y-01 | 707 |
| synthetic | Y-02 | 44 |
| synthetic | Y-04 | 707 |
| synthetic | Y-05 | 707 |
| synthetic | Y-06 | 991 |
| synthetic | Y-07 | 298 |

## 검증

### V1 복사 — 통과

```
{
 "checks": {
  "나이": 707,
  "ER 판정": 707,
  "PR 판정": 707,
  "pT": 707,
  "pM": 476,
  "병기군": 707,
  "HER2 IHC 점수": 438
 },
 "mismatch": []
}
```

### V2 계산 — 통과

```
{
 "n": 707,
 "mismatch": []
}
```

### V3 분포 — 통과

```
{
 "폐경 (실제 %, 다시 만든 %, 779명)": {
  "premenopausal": [
   23.5,
   23.0
  ],
  "postmenopausal": [
   72.7,
   72.9
  ],
  "perimenopausal": [
   3.9,
   4.1
  ]
 },
 "폐경 최대 차이 %p": 0.5,
 "receptors.er_percent 구간 최대 차이 %p (경계 밖 양성 331명)": 2.1,
 "receptors.pr_percent 구간 최대 차이 %p (경계 밖 양성 233명)": 2.1,
 "기준 %p": 5.0
}
```

### V4 관계 — 통과

```
{
 "Ki-67 높음 비율 (PAM50별)": {
  "BRCA_Her2": 0.8,
  "BRCA_LumA": 0.27,
  "BRCA_Normal": 0.32,
  "BRCA_LumB": 0.71,
  "BRCA_Basal": 0.75,
  "?": 0.36
 },
 "grade 3 비율 (아형별)": {
  "HER2+": 0.56,
  "HR+/HER2-": 0.21,
  "TNBC": 0.71
 },
 "기대": "LumA < LumB, HR+/HER2- < TNBC"
}
```

### V6 이미지 좌표 — 통과

```
{
 "n": 761,
 "mismatch": []
}
```
