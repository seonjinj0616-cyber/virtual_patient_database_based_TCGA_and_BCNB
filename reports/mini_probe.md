# mini 점검 — TCGA ① 차트

차트 675건 · mini는 읽기만 함

## error

| 값 | 수 |
|---|---|

## marker

| 값 | 수 |
|---|---|
| ('PD-L1', 'not_recorded') | 675 |
| ('ESR1', 'negative') | 654 |
| ('PALB2', 'negative') | 654 |
| ('gBRCA1', 'negative') | 647 |
| ('gBRCA2', 'negative') | 644 |
| ('AKT1', 'negative') | 641 |
| ('PTEN', 'negative') | 629 |
| ('ER', 'positive') | 522 |
| ('PR', 'positive') | 470 |
| ('PIK3CA', 'negative') | 446 |
| ('HER2', 'low') | 435 |
| ('Ki-67', 'positive') | 389 |
| ('Ki-67', 'negative') | 286 |
| ('PR', 'negative') | 205 |
| ('PIK3CA', 'positive') | 162 |
| ('ER', 'negative') | 143 |
| ('HER2', 'positive') | 122 |
| ('HER2', 'negative') | 118 |
| ('PIK3CA', 'vus') | 51 |
| ('PTEN', 'positive') | 30 |
| ('AKT1', 'positive') | 18 |
| ('ESR1', 'not_done') | 16 |
| ('PIK3CA', 'not_done') | 16 |
| ('AKT1', 'not_done') | 16 |
| ('PTEN', 'not_done') | 16 |
| ('gBRCA1', 'not_done') | 16 |
| ('gBRCA2', 'not_done') | 16 |
| ('PALB2', 'not_done') | 16 |
| ('ER', 'low') | 10 |
| ('gBRCA2', 'vus') | 10 |

## subtype

| 값 | 수 |
|---|---|
| "HR+/HER2-" | 448 |
| "TNBC" | 105 |
| "HR+/HER2+" | 97 |
| "HR-/HER2+" | 25 |

## setting

| 값 | 수 |
|---|---|
| {"disease": "early", "line": "adjuvant", "prior_drug_classes": [], "reason": "진단 시 early / 선행·보조요법 기록 없음, 수술 먼저 함(병리 병기  | 541 |
| {"disease": "locally_advanced", "line": "adjuvant", "prior_drug_classes": [], "reason": "진단 시 locally_advanced / 선행·보조요법 | 134 |

## tests

| 값 | 수 |
|---|---|

## needs

| 값 | 수 |
|---|---|
| required | 675 |
| recommended | 675 |

## 예

```
{
 "needs required": [
  "VH-T0001",
  "VH-T0002",
  "VH-T0003"
 ],
 "needs recommended": [
  "VH-T0001",
  "VH-T0002",
  "VH-T0003"
 ]
}
```