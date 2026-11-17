"""약별 사용 분기점 표 (rules/drug_setting.csv): TCGA 투약 기록을 처방된 그대로 쓰되, 약이 어느 치료 상황에서 쓰이는지 근거를 남긴다.

1) ESMO로 나눌 수 있는 약: mini ESMO 지침 청크(data/chunks/esmo_*.json)의 setting 태그와 drugs 태그로 나눈다.
   근거는 청크 번호만 남긴다 (ESMO 원문은 저작권 때문에 이 저장소에 넣지 않는다).
2) ESMO 청크에 없는 약: FDA 라벨(DailyMed)의 적응증 절 원문을 받아 rules/labels/<약>.txt에 저장하고,
   유방암 문장으로 분기점을 정한다. 이 약들은 'ESMO 기준 아님'으로 표시한다 (나중에 구분할 수 있게).
   FDA 라벨은 미국 정부 문서라 원문을 저장해도 된다.

라벨 문장 → 분기점 (추측하지 않는 고정 규칙):
  adjuvant → 조기 예 / metastatic·advanced·recurrent → 전이성 예 / 상황 없이 'breast'만 → 구분 없음 / 'breast' 없음 → 유방암 적응증 없음

실행 (virtual_hospital 폴더, team_project 환경): python -m vh.drug_setting
"""
from __future__ import annotations

import json
import re
import urllib.parse
import urllib.request
import xml.etree.ElementTree as ET
from collections import defaultdict

from vh.common import MINI, OUT, ROOT, read_csv, write_csv

CHUNKS = [MINI / "data" / "chunks" / "esmo_chunks.json", MINI / "data" / "chunks" / "esmo_algorithm_chunks.json"]
LABELS = ROOT / "rules" / "labels"
TABLE = ROOT / "rules" / "drug_setting.csv"
DM = "https://dailymed.nlm.nih.gov/dailymed/services/v2"
INDICATIONS = "34067-9"                                   # SPL 절 코드: INDICATIONS & USAGE


def tcga_drugs() -> list[str]:
    """TCGA 세트 정답 표(truth.csv)의 실제 투약 기록에 나온 약 (mini drug_names.csv로 표준화된 이름)."""
    names = set()
    for r in read_csv(OUT / "tcga" / "truth.csv"):
        if r["항목"] == "drug_timeline" and r["값"]:
            for item in r["값"].split(" | "):
                m = re.match(r"(.+?) \[", item.strip())
                if m:
                    names |= {d.strip() for d in m.group(1).split("+") if d.strip() and d.strip() != "unknown"}
    return sorted(names)


def esmo_index() -> dict[str, dict[str, list[str]]]:
    idx: dict = defaultdict(lambda: defaultdict(list))
    for f in CHUNKS:
        for c in json.loads(f.read_text(encoding="utf-8")):
            if c.get("superseded_by"):
                continue
            for d in c.get("drugs") or []:
                for s in c.get("setting") or []:
                    idx[d]["early" if s in ("early", "locally_advanced") else s].append(c["chunk_id"])
    return idx


def get(url: str) -> bytes:
    with urllib.request.urlopen(url, timeout=60) as r:
        return r.read()


def label(drug: str) -> dict | None:
    """DailyMed에서 유방암 적응증 문장이 있는 라벨을 찾는다 (앞 10개 중 'breast'가 든 첫 라벨). 없으면 첫 라벨."""
    q = urllib.parse.quote(drug)
    spls = json.loads(get(f"{DM}/spls.json?drug_name={q}&pagesize=10"))["data"]
    first = None
    for s in spls:
        root = ET.fromstring(get(f"{DM}/spls/{s['setid']}.xml"))
        for sec in root.iter("{urn:hl7-org:v3}section"):
            code = sec.find("{urn:hl7-org:v3}code")
            if code is not None and code.get("code") == INDICATIONS:
                text = re.sub(r"\s+", " ", "".join(sec.itertext())).strip()
                got = {"setid": s["setid"], "title": s["title"], "published": s["published_date"], "text": text}
                if re.search(r"breast", text, re.I):
                    return got
                first = first or got
                break
    return first


def classify(text: str) -> tuple[str, str, str]:
    """(조기, 전이성, 근거 문장). 라벨 문장에서 'breast'가 든 문장만 본다."""
    sents = [s.strip() for s in re.split(r"(?<=[.;])\s+", text) if re.search(r"breast", s, re.I)]
    if not sents:
        return "유방암 적응증 없음", "유방암 적응증 없음", ""
    joined = " ".join(sents)
    early = "예" if re.search(r"adjuvant", joined, re.I) else None
    met = "예" if re.search(r"metasta|advanced|recurren", joined, re.I) else None
    if early is None and met is None:
        return "구분 없음", "구분 없음", sents[0]
    return early or "라벨에 없음", met or "라벨에 없음", sents[0]


def main() -> int:
    drugs, idx = tcga_drugs(), esmo_index()
    classes = {r["generic_name"]: r for r in read_csv(MINI / "data" / "dictionaries" / "drug_classes.csv")}
    LABELS.mkdir(parents=True, exist_ok=True)
    rows = []
    for d in drugs:
        c = classes.get(d, {})
        base = {"generic_name": d, "drug_class": c.get("drug_class", ""), "drug_subclass": c.get("drug_subclass", "")}
        if d in idx:
            e, m = idx[d].get("early", []), idx[d].get("metastatic", [])
            rows.append({**base, "근거": "ESMO", "조기 (선행·보조)": "예" if e else "ESMO에 없음",
                         "전이성": "예" if m else "ESMO에 없음", "ESMO 청크 (조기)": " ".join(sorted(set(e))[:8]),
                         "ESMO 청크 (전이성)": " ".join(sorted(set(m))[:8]), "외부 근거": "", "근거 문장": "",
                         "ESMO 기준 아님": "", "상태": "자동 (C 청크 태그)"})
            continue
        lab = label(d)
        if lab is None:
            rows.append({**base, "근거": "없음", "조기 (선행·보조)": "근거 없음", "전이성": "근거 없음",
                         "외부 근거": "DailyMed 라벨 없음 (허가 전 임상시험 약일 수 있음)", "근거 문장": "",
                         "ESMO 기준 아님": "예", "상태": "근거 찾아야 함"})
            continue
        f = LABELS / f"{d.replace(' ', '_')}.txt"
        f.write_text(f"title: {lab['title']}\nsetid: {lab['setid']}\npublished: {lab['published']}\n"
                     f"url: https://dailymed.nlm.nih.gov/dailymed/drugInfo.cfm?setid={lab['setid']}\n\n{lab['text']}\n",
                     encoding="utf-8", newline="\n")
        e, m, quote = classify(lab["text"])
        rows.append({**base, "근거": "FDA 라벨", "조기 (선행·보조)": e, "전이성": m, "외부 근거":
                     f"{lab['title'][:80]} (setid {lab['setid']}, {lab['published']}) → rules/labels/{f.name}",
                     "근거 문장": quote, "ESMO 기준 아님": "예", "상태": "검토 전"})
    cols = ["generic_name", "drug_class", "drug_subclass", "근거", "조기 (선행·보조)", "전이성", "ESMO 청크 (조기)",
            "ESMO 청크 (전이성)", "외부 근거", "근거 문장", "ESMO 기준 아님", "상태"]
    write_csv(TABLE, rows, cols)
    n = defaultdict(int)
    for r in rows:
        n[r["근거"]] += 1
    print(f"약 {len(rows)}가지: " + ", ".join(f"{k} {v}" for k, v in n.items()) + f" → {TABLE}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
