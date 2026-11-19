# virtual_hospital — TCGA·BCNB 기반 가상 병원 DB

> A virtual hospital environment built on synthetic breast cancer patients derived from the TCGA-BRCA and BCNB datasets (no original data included).

작성: 2026-11-09 (A) · 최종 갱신: 2026-11-19 · 상태: **작업 끝남 (2026-11-19)**

> **이 저장소는 더 고치지 않는다.** 2026-11-19에 코드와 데이터를 처방 모듈 저장소 [`Br-CDSS-Konyang-University-bootcamp/prescription_model_breast_cancer`](https://github.com/Br-CDSS-Konyang-University-bootcamp/prescription_model_breast_cancer)의 `src/virtual_hospital/`·`data/virtual_hospital/`로 옮겼고, 이후 작업은 그쪽에서 한다 (아래 "옮긴 곳"). 여기서 한 일 전체: [notes/progress.md](notes/progress.md)

TCGA-BRCA와 BCNB의 실제 값을 뼈대로, 데이터에 없는 칸만 근거 있는 규칙으로 채운 가상 유방암 환자다. 처방 모듈(입력 → 바이오마커 → 확정 → 지침 검색·추천·급여)을 실제 슬라이드가 붙은 환자로 끝까지 돌려 보려고 만들었다.

## 마지막 상태 (2026-11-19)

| | TCGA ① 수술 후 | TCGA ② 재발 | BCNB 수술 전 |
|---|---|---|---|
| 가상환자 | **671명** | **9명** (원격 재발 13명 중) | **971명** (1,058명 중) |
| 장면 (판정 기준일) | 실제 첫 보조 투약일과 수술 후 49일 중 빠른 날 → 보조 요법 결정 | 실제로 다음 고식 치료를 정한 날 → 내분비 2차 결정 3, 항암 1차 결정 6 | 초진일 → 선행요법 여부 결정 |
| 차트 | 외래 경과기록 + 수술 병리 + 분자병리 | ① + 재발 경과기록 + 투약 기록 | 초진 기록 + 중심 생검 병리 + 유방 초음파 |
| 이 저장소에 | `out/tcga/` | `out/tcga_recur/` | **없음** (BCNB 약관, `local/`에만) |

- 검증 V1~V4·V6, 관문 G1~G7 (처방 모듈 입력 모듈 재현 포함) 통과, 테스트 9개 통과
- 모든 차트에 확정 상태 초안 `expected/confirmed_state.json` (처방 흐름의 입력)
- 입력 모듈 LLM 시험 (qwen3:14b, 59명): 필드 정확도 98.8%
- 처방 흐름 시험 (49명): 모두 오류 없이 끝까지 돌았다. 고칠 거리 8가지는 [notes/progress.md](notes/progress.md) §3

## 원칙

- **실제 값 먼저.** 없는 값만 합성하고 칸마다 `real` / `derived` / `synthetic`과 거친 규칙 id를 남긴다. 합성 근거 순위: ① 같은 환자 계산 → ② 같은 데이터 안 분포 → ③ 같은 환자 대리 지표 → ④ 문헌 → ⑤ 고정값
- **처방 모듈을 고치지 않는다.** 생성기가 처방 모듈 입력 규칙에 맞추고, 실제 값이 못 맞추면 그 환자를 뺀다
- **결정 시점마다 차트.** 차트에는 판정 기준일 전에 일어난 일만 쓰고, 그날부터의 값(수술 림프절, 이후 투약, 생존)은 `truth.csv`에만 둔다
- **실제 처방 기록은 참고용이다.** 2000년대 미국 처방이라 정답이 아니다
- **BCNB에서 나온 것은 git에 올리지 않는다.** 약관상 수정본도 재배포할 수 없다

## 폴더 구조

```
virtual_hospital/
├── README.md                         이 문서
├── vh/                               ← git: 코드
│   ├── common.py                     경로, 규칙 표 읽기, vp 번호로 정한 난수
│   ├── tcga.py                       TCGA 고르기·옮기기·계산·합성 (처방 모듈의 TCGA 변환기를 불러 씀)
│   ├── render.py · gates.py · verify.py   chart.txt, 관문 G, 검증 V
│   ├── build.py · tcga_recur.py · bcnb.py · confirmed.py   만들기 (아래 "만드는 순서")
│   ├── fetch_hgvsc.py · fetch_thennavan.py                 자료 받기
│   ├── export_mini.py                처방 모듈 저장소로 TCGA 차트·표 복사 (BCNB 제외)
│   └── bcnb_check.py · mini_probe.py · llm_run.py          점검·시험
├── rules/                            ← git: rules.csv(규칙 원본 69개), references.csv(문헌 값),
│                                        thresholds.csv, phrases.csv, image_tables.csv
├── data/
│   ├── tcga_hgvsc.csv                ← git: 변이 c. 표기 (fetch_hgvsc가 만듦)
│   └── BCNB/BCNB/                    ← git 제외: BCNB 원자료 37GB (각자 받음: WSIs/, patient-clinical-data.xlsx)
├── out/                              ← git
│   ├── tcga/                         TCGA ① : patients·fields·truth.csv, NOTICE.md, images/(이미지 표 틀)
│   │   └── charts/<VH-T…>/chart.txt, expected/{patient_state, biomarker_record, confirmed_state}.json
│   └── tcga_recur/                   TCGA ② : 위와 같은 구성 + treatments.csv
├── reports/                          ← git: 생성 보고, 뺀 환자, 관문 결과, mini 점검
├── notes/                            ← git: 설계·기준·기록 (아래 "문서")
├── tests/test_vh.py                  ← git: 규칙 id ↔ 표, 다시 만들면 같은지, mini check
└── local/                            ← git 제외
    ├── bcnb/                         BCNB 차트·정답·이미지 표 (각자 만듦, out/tcga/와 같은 구성)
    ├── reports/                      BCNB 보고
    ├── source_map.csv · slide_map.csv   가상 번호 ↔ 원본 ID·슬라이드
    ├── thennavan2021/                등급 판독 원본 (CC BY-NC-ND, fetch_thennavan이 받음)
    └── llm_runs/                     입력 모듈 LLM 시험 결과
```

## 만드는 순서

이 저장소만으로는 돌지 않는다. 같은 상위 폴더에 `team_project_mini`(처방 모듈, 읽기만 함)와 `team_project_final`(모듈 1: MKI67 발현, 슬라이드 QC·썸네일)이 있어야 하고, mini의 `team_project` 환경에서 이 폴더를 작업 폴더로 실행한다.

**mini는 `ff86fcd`(2026-11-18) 또는 그 전으로 둔다.** `vh/tcga.py`·`vh/fetch_hgvsc.py`가 mini의 옛 TCGA 변환기(`src/input/script/tcga/`)와 `data/tcga_brca/`를 읽는데, mini가 `cd3510d`(2026-11-18)에서 둘 다 지웠다. 옮긴 쪽은 그 사본을 가지고 있어서 지금 mini에서도 돈다.

| 단계 | 명령 | 읽는 것 | 만드는 것 | 언제 |
|---|---|---|---|---|
| 0 | `python -m vh.fetch_thennavan` | Europe PMC | `local/thennavan2021/mmc3.xlsx` | 처음 한 번 (1단계의 grade 판독 점수) |
| 1 | `python -m vh.build` | mini TCGA 크롭본·병합본·변환기, `data/tcga_hgvsc.csv`, `local/thennavan2021/`, `team_project_final` | `out/tcga/`, `reports/`, `local/source_map.csv`·`slide_map.csv` | 규칙·코드를 바꿀 때마다 |
| (1-1) | `python -m vh.fetch_hgvsc` | `local/source_map.csv`, mini `data/tcga_brca/cbioportal/mutations.tsv`, GDC·Genome Nexus | `data/tcga_hgvsc.csv` | 변이 표기가 없을 때만 (git에 있음). 받은 뒤 1단계를 다시 |
| 2 | `python -m vh.tcga_recur` | 1단계와 같은 원본 (TCGA ①을 다시 계산해 씀) | `out/tcga_recur/` | 1단계 뒤 |
| 3 | `python -m vh.bcnb` | `data/BCNB/BCNB/`, TCGA 분포(Allred·폐경) | `local/bcnb/`, `local/reports/` | BCNB 원자료를 받은 사람만 |
| 4 | `python -m vh.confirmed` | 1~3단계의 `charts/*/expected/` | 차트마다 `expected/confirmed_state.json`, `reports/confirmed.md` | **마지막에** (1·2단계가 차트 폴더를 새로 만들어서) |
| 5 | `python -m pytest tests` | 위 결과 | — | 만들 때마다 |
| 6 | `python -m vh.export_mini` | `out/` | mini `data/virtual_hospital/` (BCNB 제외, 매번 비우고 새로 씀) | 처방 모듈에서 쓸 때 (옮긴 뒤로는 필요 없음) |

점검·시험 (필요할 때):

- `python -m vh.bcnb_check data/BCNB/BCNB`: BCNB 원자료 점검 (개수·ID만)
- `python -m vh.mini_probe`: 정답을 B `assess`와 화면 1 초안에 넣어 `unknown`·빈 칸을 셈
- `python -m vh.llm_run`: 차트를 입력 모듈 LLM으로 끝까지 돌리고 채점 (GPU 터널 필요)

## 옮긴 곳 (처방 모듈 저장소, 2026-11-19부터)

```
src/virtual_hospital/                 ← vh/ (+ notes/), tcga_convert.py(옛 TCGA 변환기 사본) 추가
data/virtual_hospital/
├── rules/                            ← rules/
├── source/                           ← mini data/tcga_brca/의 크롭본·병합본 CSV 사본
├── tcga_hgvsc.csv                    ← data/tcga_hgvsc.csv
├── tcga/, tcga_recur/                ← out/tcga/, out/tcga_recur/
├── reports/                          ← reports/
└── local/                            ← local/ (git 제외)
    ├── bcnb_raw/                     ← data/BCNB/BCNB/ (Windows에서 local/BCNB/가 local/bcnb/와 겹쳐 이름을 바꿈)
    ├── bcnb/ · reports/ · thennavan2021/ · llm_runs/ · source_map.csv · slide_map.csv
    ├── features/                     (옮긴 뒤 추가) 슬라이드 벡터 .npz
    └── virtual_hospital.db           (옮긴 뒤 추가) 가상 병원 DB 한 파일
tests/virtual_hospital/               ← tests/
```

실행은 그쪽 `team_project` 폴더에서 `python -m src.virtual_hospital.<이름>`이다.

## 문서

| 문서 | 내용 |
|---|---|
| [notes/progress.md](notes/progress.md) | 2026-11-09 ~ 11-19 한 일, 사용자 결정, 처방 흐름 시험 결과, 남은 것 |
| [notes/design.md](notes/design.md) | 설계: 규칙 체계, 시점과 정답 분리, 칸별 규칙, 결측, CSV·chart.txt, 이미지, 검증·관문 |
| [notes/synthetic_criteria.md](notes/synthetic_criteria.md) | 칸별로 어떻게 합성했는지, 실제 값을 바꾼 것, 문헌 값 |
| [notes/build_guide.md](notes/build_guide.md) | 규칙 문서·코드 안내, 처방 모듈에서 쓰는 파일 |
| [notes/bcnb_check.md](notes/bcnb_check.md) | BCNB 원자료 점검 |
| [notes/mini_findings.md](notes/mini_findings.md) | 처방 모듈 점검 결과 (읽기만) |
| [notes/module_result_format_proposal.md](notes/module_result_format_proposal.md) | 이미지 모듈 결과 형식 제안 (팀 합의 전) |

## 데이터 출처와 인용

이 저장소에는 원본 데이터가 들어 있지 않다. 각 데이터는 아래 출처에서 받아야 하며, 쓸 때는 함께 인용한다.

**TCGA-BRCA**

The results shown here are in whole or part based upon data generated by the TCGA Research Network: https://www.cancer.gov/tcga.

- Grossman RL, et al. Toward a shared vision for cancer genomic data. N Engl J Med. 2016;375(12):1109-1112. doi:10.1056/NEJMp1607591 (GDC)
- Liu J, et al. An integrated TCGA pan-cancer clinical data resource to drive high-quality survival outcome analytics. Cell. 2018;173(2):400-416.e11. doi:10.1016/j.cell.2018.02.052 (생존 자료)
- Cerami E, et al. The cBio cancer genomics portal: an open platform for exploring multidimensional cancer genomics data. Cancer Discov. 2012;2(5):401-404. doi:10.1158/2159-8290.CD-12-0095
- Gao J, et al. Integrative analysis of complex cancer genomics and clinical profiles using the cBioPortal. Sci Signal. 2013;6(269):pl1. doi:10.1126/scisignal.2004088

**BCNB**

- Xu F, Zhu C, Tang W, et al. Predicting axillary lymph node metastasis in early breast cancer using deep learning on primary tumor biopsy slides. Front Oncol. 2021;11:759007. doi:10.3389/fonc.2021.759007 · https://bupt-ai-cz.github.io/BCNB/
- BCNB 약관(원본·수정본 재배포 금지)에 따라 이 저장소에는 BCNB 원본과 BCNB로 만든 가상환자 기록·차트·정답·주석을 넣지 않는다 (`data/BCNB/`, `local/`은 git 제외). BCNB를 쓰는 코드는 비상업 연구 목적에 한한다.

**조직학적 등급 (TCGA, 병리 전문의 판독)**

- Thennavan A, Beca F, Xia Y, et al. Molecular analysis of TCGA breast cancer histologic types. Cell Genomics. 2021;1(3):100067. doi:10.1016/j.xgen.2021.100067 · Data S2 (`mmc3.xlsx`, 조직 소견 11가지 점수)
- Heng YJ, et al. The molecular basis of breast cancer pathological phenotypes. J Pathol. 2017;241(3):375-391. PMID 27861902 (판독 채점표)
- Data S2는 CC BY-NC-ND 4.0이라 원본은 `local/thennavan2021/`에만 둔다 (git 제외, `python -m vh.fetch_thennavan`으로 Europe PMC에서 받음). 가상환자 차트에는 그 판독 점수로 정한 등급과 세 점수(관 형성·핵 다형성·유사분열)를 쓴다 (규칙 M-05, 650명). 판독이 없는 21명은 합성(Y-05). 자세한 출처와 표시: [out/tcga/NOTICE.md](out/tcga/NOTICE.md)

**변이 주석**

- de Bruijn I, et al. Genome Nexus: a comprehensive resource for the annotation and interpretation of genomic variants in cancer. JCO Clin Cancer Inform. 2022;6:e2100144. doi:10.1200/CCI.21.00144

**합성 값의 문헌 근거** (Ki-67, 판독 점수 없는 환자의 grade, ECOG, 겨드랑이 초음파): 숫자와 출처, 표 번호는 [rules/references.csv](rules/references.csv)

## 주의

- 연구·교육용 가상 데이터다. 진단·처방에 쓰지 않는다
- 차트의 이름·등록번호·주민번호는 모두 가짜다
- 차트 글은 로컬 모델에서만 처리한다 (외부 API 금지)
