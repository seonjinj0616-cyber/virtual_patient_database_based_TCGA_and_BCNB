"""TCGA ② 재발 갈래: 실제 원격 재발이 있는 환자를 재발 외래 시점 차트로 만든다 (투약 기록 포함).

- 진단 시 값(병리·수용체·변이·합성 칸)은 TCGA ① 생성(tcga.build_all)을 그대로 쓴다
- 판정 기준일 = 원격 전이일 + 14일 (D-R1). 그날까지 시작한 실제 투약만 차트에 쓰고, 뒤의 투약은 정답 표로
- 투약은 처방된 그대로 (mini 변환기의 treatment_history: 약, 구분, 시작·종료일, 주기, 반응)
- 중단 사유는 실제 값으로만 정한다 (D-R2). 근거가 없으면 비운다 → 차수는 mini lines.annotate가 계산

실행 (virtual_hospital 폴더, team_project 환경): python -m vh.tcga_recur
결과: out/tcga_recur/ (patients·fields·treatments·truth CSV, charts/), reports/tcga_recur*.csv·md
"""
from __future__ import annotations

import collections
import json
import shutil

from vh import gates, render
from vh.common import MINI, OUT, REPORTS, Rec, read_csv, write_csv
from vh.tcga import build_all, entry

INDEX_AFTER_METASTASIS = 14                    # D-R1: 재발 외래 = 원격 전이일 + 14일 (VC-0103 간격과 비슷)
ADJ_ENDOCRINE_DONE = 1640                      # D-R2: 보조 내분비를 약 4.5년(1,640일) 이상 쓰면 완료
SWITCH_GAP = 35                                # D-R2: 보조 항암 끝나고 35일 안에 다른 보조 항암 시작 → 계획된 변경
RECUR_GAP = 31                                 # D-R2: 전이일 31일 전 이후에 끝났거나 계속 중이면 재발로 중단 (진행)
STANDARD_INTERVALS = (7, 14, 21, 28)           # 차트 주기 표기 (weekly·q2w·q3w·q4w)
OUT_DIR = OUT / "tcga_recur"


def classes() -> dict[str, tuple[str, str]]:
    """성분명 → (drug_class, drug_subclass), mini drug_classes.csv."""
    return {r["generic_name"]: (r["drug_class"], r["drug_subclass"])
            for r in read_csv(MINI / "data" / "dictionaries" / "drug_classes.csv")}


def merge(items: list[dict]) -> list[dict]:
    """D-R4: TCGA는 병용 약을 약마다 한 줄로 적는다. 구분·시작일·종료일이 같은 줄은 한 요법(예: AC)으로 묶는다.
    주기·반응은 모든 약이 같을 때만 남긴다 (다르면 비움)."""
    groups: dict[tuple, list[dict]] = {}
    for t in items:
        groups.setdefault((t["setting"], t.get("start_day"), t.get("end_day")), []).append(t)
    out = []
    for g in groups.values():
        same = lambda k: g[0].get(k) if all(x.get(k) == g[0].get(k) for x in g) else None  # noqa: E731
        out.append({**g[0], "drugs": [d for x in g for d in x["drugs"]], "cycles": same("cycles"),
                    "best_response": same("best_response")})
    return sorted(out, key=lambda t: (t.get("start_day") is None, t.get("start_day") or 0))


def stop_reason(i: int, items: list[dict], mday: int, cls: dict) -> tuple[str | None, str]:
    """D-R2: (중단 사유, 근거). 실제 값으로만 정하고, 근거가 없으면 (None, '근거 없음')."""
    t = items[i]
    sub = lambda u: {cls.get(d, ("", ""))[1] for d in u["drugs"]}  # noqa: E731
    kinds = {cls.get(d, ("", ""))[0] for d in t["drugs"]}
    s, e = t.get("start_day"), t.get("end_day")
    if t.get("best_response") == "PD":
        return "progression", "실제 반응 PD"
    if t["setting"] != "palliative" and s is not None and s < mday and e is not None and e >= mday - RECUR_GAP:
        return "progression", (f"전이 {mday - e}일 전까지 투약 (재발로 중단)" if e < mday
                               else f"전이 {e - mday}일 뒤까지 투약 (재발로 중단)")
    if t["setting"] == "adjuvant" and kinds == {"Hormone Therapy"} and s is not None and e is not None             and e - s >= ADJ_ENDOCRINE_DONE:
        return "completed", f"보조 내분비 {e - s}일 복용"
    if t["setting"] in ("adjuvant", "neoadjuvant") and "anthracycline" in sub(t) and e is not None:
        nxt = [u for u in items[i + 1:] if u["setting"] == t["setting"] and u.get("start_day") is not None
               and u["start_day"] > s and 0 <= u["start_day"] - e <= SWITCH_GAP and "taxane" in sub(u)]
        if nxt:
            return "planned_switch", f"안트라사이클린 끝나고 {nxt[0]['start_day'] - e}일 뒤 탁산 시작 (순차 요법)"
    return None, "근거 없음 (비움)"


def treatments(ps: dict, index_day: int, mday: int, cls: dict) -> tuple[list[dict], list[dict], list[str]]:
    """(차트에 쓸 요법, 정답 표로 가는 뒤 요법, 문제)."""
    items = merge(ps["fields"].get("treatment_history") or [])
    anthra = ps["fields"]["anthracycline_drug_dose"]["drugs"]
    shown, later, problems = [], [], []
    for i, t in enumerate(items):
        if t.get("start_day") is None:
            problems.append(f"투약 시작일 없음: {'+'.join(t['drugs'])}")
            continue
        if t["start_day"] > index_day:
            later.append(t)
            continue
        cyc = t.get("cycles")
        if cyc and cyc.get("basis") != "recorded":
            cyc = None                                           # 추정 주기 수는 차트에 쓰지 않는다
        elif cyc and (cyc.get("interval_basis") != "derived" or cyc.get("interval_days") not in STANDARD_INTERVALS):
            cyc = {**cyc, "interval_days": None, "interval_basis": None}   # 약 표준 간격(standard)은 쓰지 않는다
        elif cyc:
            cyc = {**cyc, "interval_basis": "recorded"}          # 실제 날짜로 계산한 간격을 차트에 적었으므로 차트 기준 recorded
        doses = {}
        for g in t["drugs"]:
            if cls.get(g, ("", ""))[1] != "anthracycline":
                continue
            a = [x for x in anthra if x["drug"] == g]
            if len(a) != 1 or not isinstance(a[0]["dose_per_admin"], dict):
                problems.append(f"{g} 1회 용량 없음 또는 여러 줄: mini가 용량 없는 안트라사이클린 줄을 schema 위반으로 냄")
                continue
            doses[g] = a[0]["dose_per_admin"]
        reason, why = stop_reason(i, items, mday, cls)
        ongoing = t.get("end_day") is not None and t["end_day"] > index_day
        resp = t.get("best_response") if t.get("best_response") in ("CR", "PR", "SD", "PD") else None
        if ongoing and resp == "PD":
            problems.append(f"{'+'.join(t['drugs'])}: 투약 중인데 실제 반응 PD — mini가 반응 칸 PD를 중단 사유 '진행'으로 읽음")
        shown.append({"drugs": t["drugs"], "setting": t["setting"], "start_day": t["start_day"],
                      "end_day": None if ongoing else t.get("end_day"), "ongoing": ongoing, "cycles": cyc,
                      "best_response": resp, "stop_reason": None if ongoing else reason, "doses": doses,
                      # D-R3: mini 읽기 규칙과 같게 — 진행이면 투약 기간 안 전이일, 없으면 종료일
                      "progression_day": None if ongoing or reason != "progression" else
                      mday if t["start_day"] <= mday <= (t.get("end_day") if t.get("end_day") is not None else mday) else t.get("end_day"),
                      "adjuvant_endocrine": t["setting"] == "adjuvant"
                      and any(cls.get(g, ("", ""))[0] == "Hormone Therapy" for g in t["drugs"]),
                      "stop_basis": "판정 기준일에 투약 중" if ongoing else why})
    return shown, later, problems


def main() -> int:
    pts, _, pss, _ = build_all()
    cls, env = classes(), gates.envelope(pss)
    if (OUT_DIR / "charts").exists():
        shutil.rmtree(OUT_DIR / "charts")
    kept, dropped, rows_t = [], [], []
    for p in pts:
        ps0 = pss[p.source_id]
        rec = entry(ps0, "recurrence.status")
        if rec.get("value") != "distant":
            continue
        mday = entry(ps0, "recurrence.metastasis_day").get("value")
        rday = entry(ps0, "recurrence.recurrence_day").get("value")
        sites = entry(ps0, "recurrence.metastatic_sites").get("value") or []
        problems = list(p.problems)
        if mday is None:
            problems.append("원격 전이일 없음")
        elif rday not in (None, mday):
            problems.append(f"국소 재발({rday}일)이 원격 전이({mday}일)보다 먼저: 이 갈래에서 다루지 않음")
        if not sites or any(s not in render.SITE_KO for s in sites):
            problems.append(f"전이 부위를 차트로 쓸 수 없음: {sites}")
        if problems:
            dropped.append({"vp_id": p.vp_id, "reason": "; ".join(problems)})
            continue
        p.branch, p.index_day = "TCGA_recur", mday + INDEX_AFTER_METASTASIS
        p.recs.pop("recurrence.status", None)
        p.add(Rec("recurrence.status", "present", "distant", "real", rule_id="M-01", source_column="recurrence_status"))
        p.add(Rec("recurrence.metastatic_sites", "present", sites, "real", rule_id="M-01", source_column="nte_sites"))
        p.add(Rec("recurrence.metastasis_day", "present", mday, "real", rule_id="M-01", source_column="metastasis_dx_days"))
        p.add(Rec("recurrence.recurrence_day", "present", mday, "real", rule_id="M-01", source_column="metastasis_dx_days"))
        p.add(Rec("recurrence.recurrence_date", "present", render.Chart(p.vp_id, p.dx_date, 0).on(mday), "derived", "①",
                  "D-01", note="가짜 진단일 + 실제 전이 일수"))
        p.treatments, later, tproblems = treatments(ps0, p.index_day, mday, cls)
        ends = [t for t in p.treatments if t["adjuvant_endocrine"] and t["end_day"] is not None and not t["ongoing"]]
        if ends:
            e = max(t["end_day"] for t in ends)
            p.add(Rec("recurrence.adjuvant_endocrine_end_date", "present", render.Chart(p.vp_id, p.dx_date, 0).on(e),
                      "derived", "①", "D-R2", source_column="drug_end_days", note="보조 내분비 투약 줄의 실제 종료일"))
        if tproblems:
            dropped.append({"vp_id": p.vp_id, "reason": "; ".join(tproblems)})
            continue
        try:
            text, ps, errs = render.chart(p)
        except render.RenderError as ex:
            dropped.append({"vp_id": p.vp_id, "reason": f"G2 표기 없음: {ex}"})
            continue
        res = gates.run(p, ps, errs, env, text)
        if res["failed"]:
            dropped.append({"vp_id": p.vp_id, "reason": "; ".join(f"{k}: {res[k][0]}" for k in res["failed"])})
            continue
        d = OUT_DIR / "charts" / p.vp_id
        (d / "expected").mkdir(parents=True, exist_ok=True)
        (d / "chart.txt").write_text(text, encoding="utf-8", newline="\n")
        (d / "expected" / "patient_state.json").write_text(json.dumps(ps, ensure_ascii=False, indent=2) + "\n",
                                                           encoding="utf-8", newline="\n")
        (d / "expected" / "biomarker_record.json").write_text(
            json.dumps(res["biomarker"], ensure_ascii=False, indent=2) + "\n", encoding="utf-8", newline="\n")
        lines = {(t.get("start_day"), tuple(t["drugs"])): t for t in ps["fields"]["treatment_history"]}
        for t in p.treatments:
            g = lines.get((t["start_day"], tuple(t["drugs"])), {})
            rows_t.append({"vp_id": p.vp_id, "drugs": "+".join(t["drugs"]), "setting": t["setting"],
                           "start_day": t["start_day"], "end_day": t["end_day"], "stop_reason": t["stop_reason"] or "",
                           "stop_basis": t["stop_basis"], "best_response": t["best_response"] or "",
                           "line (mini 계산)": g.get("line"), "rule_id": "M-01, D-R2"})
        p.truth["later_treatments"] = " | ".join(f"{'+'.join(t['drugs'])} d{t['start_day']}" for t in later)
        kept.append((p, ps))

    write_csv(OUT_DIR / "patients.csv", [{"vp_id": p.vp_id, "branch": p.branch, "dx_date": p.dx_date,
                                          "index_day": p.index_day, "metastasis_day": p.recs["recurrence.metastasis_day"].value,
                                          "sex": "F", "age": p.recs["patient.age"].value} for p, _ in kept])
    write_csv(OUT_DIR / "fields.csv", [r.row(p.vp_id) for p, _ in kept for r in p.recs.values()])
    write_csv(OUT_DIR / "treatments.csv", rows_t)
    write_csv(OUT_DIR / "truth.csv", [{"vp_id": p.vp_id, "항목": k, "값": "" if v is None else v}
                                      for p, _ in kept for k, v in p.truth.items()])
    write_csv(REPORTS / "tcga_recur_excluded.csv", dropped, ["vp_id", "reason"])
    lines = collections.Counter((ps["fields"].get("at_index") or {}).get("line") for _, ps in kept)
    summary = {"세트": len(kept), "뺀 환자": len(dropped), "요법 줄": len(rows_t),
               "중단 사유": dict(collections.Counter(r["stop_reason"] or "(비움)" for r in rows_t)),
               "중단 사유 근거": dict(collections.Counter(r["stop_basis"].split(" (")[0].split(" ")[0] for r in rows_t)),
               "뺀 이유": dict(collections.Counter(r["reason"].split(":")[0][:20] for r in dropped))}
    (REPORTS / "tcga_recur.md").write_text("# TCGA ② 재발 갈래 — 생성 보고\n\n```\n" +
                                           json.dumps(summary, ensure_ascii=False, indent=1) + "\n```\n",
                                           encoding="utf-8", newline="\n")
    print(json.dumps(summary, ensure_ascii=False))
    for r in dropped:
        print("뺌", r["vp_id"], r["reason"][:150])
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
