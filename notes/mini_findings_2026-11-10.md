# mini 처방 모듈 점검 결과 2026-11-10 (mini는 고치지 않음)

작성: 2026-11-10 (A) · mini 커밋 `0a1488e` (`input/rename-palliative-setting`), 읽기만 함
근거: 관문 G7(입력 모듈 재현), `python -m vh.mini_probe` (B `assess` + 화면 1 초안 `build_draft`를 TCGA 675건·BCNB 971건에 돌림). 결과 `reports/mini_probe.md`, `local/reports/mini_probe_bcnb.md`

C 지침 검색, B `recommend()`(LLM), D 급여 판정은 Qdrant·LLM이 필요해 돌리지 않았다.

## 1. 입력 모듈 (A) — 차트를 읽는 규칙 (`src/input/script/pipeline.py`)

| 번호 | 문제 | 이 폴더에서 한 처리 | 영향 |
|---|---|---|---|
| H1 | `_tnm`이 `TX`·`NX`·`MX`를 `MX` 그대로 낸다. 스키마(`tnm_value`) 설명과 TCGA 변환기는 `not_assessed` | MX + I~III기 → M0 (D-06), NX 제외 (S-08) | 실제 차트에 MX가 오면 스키마 약속과 다른 값 |
| H2 | `_tnm`이 `N0(i-)`·`N0(i+)`의 꼬리표를 뗀다. 스키마 예에는 `N0(i+)`가 있다 | 정답도 뗌 (D-05) | 판정에는 영향 없음 |
| H3 | `_her2_ihc`가 점수(0~3+)만 읽는다. 점수 없이 판정만 적힌 HER2 IHC는 읽을 방법이 없다 | 같은 판정의 실제 조합으로 점수·FISH 합성 (Y-07) | 실제 차트에 "HER2 IHC: 음성"만 있으면 HER2를 못 읽음 |
| H4 | `_gene`이 `c.` 없는 변이 표기(`p.E542K`만)를 못 읽는다 | GDC에서 c. 표기를 받아 씀 (M-03). 못 찾은 33명 제외 | p.만 적힌 NGS 결과지를 못 읽음 |
| H5 | `_pct_or_range`가 `>60%`를 `percent 60`으로 읽는다 ('보다 큼'이 빠짐) | BCNB Ki-67 `＞60%`는 `61-100%`로 씀 (D-B4) | Ki-67 `>15%` 같은 표기가 오면 15%로 읽혀 판정이 바뀔 수 있음 |
| H6 | (H1을 고칠 때 같이) `confirmed.py` `_n_status`가 `n.startswith("NX")`로 평가 안 됨을 가린다. `_tnm`이 `not_assessed`를 내도록 고치면 이 검사를 지나쳐 **림프절 양성**으로 판정된다 | — | H1만 고치면 생기는 문제 |

## 2. 화면 1 초안 (`src/input/script/confirmed.py`)

| 번호 | 문제 | 영향 |
|---|---|---|
| C1 | `stage.t` 확정 칸 형식에 옛 AJCC 판의 세부 범주(`T3a`, `T2a`·`T2b` 등)가 없어 "확정 칸 형식에 없음"으로 빈칸이 된다 | TCGA 2건이 필수 칸 `stage.t` 빈칸 |
| C2 | `operable`(수술 가능 여부)이 차트에 없으면 "확인 권장"으로 남는다 | BCNB 수술 전 차트 971건 전부, TCGA 23건. **2026-11-11 처리:** BCNB 환자는 모두 실제로 수술을 받았으므로(`Surgical` 열) 초진 기록에 "수술 가능 (operable)"을 쓴다 (D-B6) → BCNB 확인 권장 0건. TCGA 23건은 수술 기록 자체가 없어 그대로 |

## 2-1. 입력 모듈 투약 기록 읽기 (2026-11-17, TCGA ② 재발 갈래에서 찾음)

| 번호 | 관찰 | 영향 |
|---|---|---|
| H7 | 투약 기록 줄에 안트라사이클린이 있는데 1회 용량이 적혀 있지 않으면 `anthracycline_drug_dose.drugs[].dose_per_admin`이 `null`이 되어 schema 검사에서 issue가 난다 (schema는 `{value, unit}` 또는 `"No value"`). `pipeline._anthracycline` | 실제 차트에 용량 없이 "AC #4"만 적힌 경우. 이 폴더에서는 해당 2명을 뺐다 (S-R1) |
| H8 | 반응 칸의 `PD`를 중단 사유 `progression`으로 읽는다 (`_stop_reason`이 날짜 뒤 글 전체를 본다). 투약 중(종료일이 없음)인데 반응이 PD인 줄도 progression이 된다 | 차수 계산이 바뀔 수 있다. 이 폴더에서는 해당 1명을 뺐다 (S-R1) |

## 3. 바이오마커 (B) — 결과로 본 것 (문제인지 확인 필요)

| 번호 | 관찰 | 질문 |
|---|---|---|
| B1 | 검사 공백 권고(`tests_needed`)가 1,646건 모두 비어 있다. 예: 수술 전 TNBC(BCNB 107건)·젊은 환자의 gBRCA 기록 없음, HR+/HER2- 조기 환자의 유전자 검사 기록 없음에서도 권고가 없다 | BM-4가 전이성에서만 도는 설계인지 |
| B2 | BCNB 수술 전 차트의 `setting.line`이 971건 모두 `unknown` ("수술 전 → 선행·수술 먼저 결정 전") | 화면 1의 `setting.phase`(수술 기록 없으면 neoadjuvant)가 대신하므로 의도된 것인지 |
| B3 | Ki-67 `intermediate` 8건 (BCNB `15-20%` 같은 구간). 판정이 안 나서 의사 확정이 필요 | 의도된 것 (구간이 20%에 걸침) |
| B4 | PIK3CA `vus` 51건 (허가 동반진단 목록에 없는 변이) | 의도된 것 |
| B5 | TCGA HER2 `low`가 435/675건 (64%). 점수 없던 198명 중 음성 판정을 1+로 합성한 경우가 들어 있다 (Y-07) | 합성값이라 처방(T-DXd 등) 점검에 쓸 때 `synthetic` 표시를 확인 |

## 4. 이 폴더(생성기)에서 고친 것

- ISH가 `equivocal`인 1명: 점수 없는 IHC 판정을 지우고 ISH로만 판정하게 했더니 B가 HER2 `unknown`을 냈다. ISH가 판정을 정할 수 있을 때(증폭·비증폭)만 IHC를 지우도록 고쳤다 (N-05). 지금 HER2 `unknown` 0건
