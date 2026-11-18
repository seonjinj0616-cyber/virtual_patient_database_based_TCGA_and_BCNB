"""처방 모듈(mini)이 가상환자를 쓰도록 필요한 파일을 mini `data/virtual_hospital/`에 복사한다.

- TCGA ①·② 차트(chart.txt, expected/*.json)와 표(patients·truth·fields·treatments CSV, NOTICE.md), 안내 문서
- BCNB는 복사하지 않는다 (약관: 수정본도 재배포 금지. mini data/의 txt·csv는 커밋될 수 있음)
- 매번 mini 쪽 `data/virtual_hospital/`을 비우고 새로 쓴다. 그 밖의 mini 파일은 건드리지 않는다

실행 (virtual_hospital 폴더, team_project 환경): python -m vh.export_mini
"""
from __future__ import annotations

import shutil

from vh.common import MINI, OUT, ROOT

DEST = MINI / "data" / "virtual_hospital"
TABLES = ("patients.csv", "truth.csv", "fields.csv", "treatments.csv", "NOTICE.md")
EXPECTED = ("patient_state.json", "biomarker_record.json", "confirmed_state.json")


def main() -> int:
    if DEST.exists():
        shutil.rmtree(DEST)
    counts = {}
    for branch in ("tcga", "tcga_recur"):
        src, dst = OUT / branch, DEST / branch
        dst.mkdir(parents=True)
        for name in TABLES:
            if (src / name).exists():
                shutil.copy2(src / name, dst / name)
        n = 0
        for d in sorted(p for p in (src / "charts").iterdir() if p.is_dir()):
            missing = [f for f in EXPECTED if not (d / "expected" / f).exists()]
            if missing:
                raise SystemExit(f"{d.name}: {missing} 없음 → vh.confirmed를 먼저 돌릴 것")
            (dst / "charts" / d.name / "expected").mkdir(parents=True)
            shutil.copy2(d / "chart.txt", dst / "charts" / d.name / "chart.txt")
            for f in EXPECTED:
                shutil.copy2(d / "expected" / f, dst / "charts" / d.name / "expected" / f)
            n += 1
        counts[branch] = n
    shutil.copy2(ROOT / "notes" / "build_guide.md", DEST / "README.md")
    print(f"복사: {DEST} — " + ", ".join(f"{k} {v}명" for k, v in counts.items()) + " (BCNB는 복사하지 않음)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
