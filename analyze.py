#!/usr/bin/env python3
"""
analyze.py — 라벨링 결과 집계

labels_*.jsonl 을 모아 일치도와 분포를 계산하고, 본 실험 파라미터를 산출한다.
외부 의존성 없음 (Fleiss κ · Cohen κ · Gwet AC1 · Wilson CI · 부트스트랩 직접 구현).

사용:
  python3 analyze.py --dir data/exp0
  python3 analyze.py --dir data/exp0 --boot 2000     # 부트스트랩 반복수

출력:
  콘솔 요약
  <dir>/analysis.json          모든 수치
  <dir>/disagreements.md       불일치 유닛 목록 (회의 안건)

판정 순서 (EXP0_PROTOCOL.md §6):
  잠정 κ 확인 → 게이트 통과 시에만 파라미터 계산.
  못 믿을 라벨로 센 m̄_norm 으로 파라미터를 뽑으면 그 파라미터도 못 믿는다.
"""

import argparse
import json
import math
import random
from collections import Counter, defaultdict
from datetime import datetime
from itertools import combinations
from pathlib import Path

# ── 사전 등록 상수 (EXP0_PROTOCOL.md §0) ──────────────────────
KAPPA_GATE = 0.61       # Landis & Koch substantial 하한
COVERAGE_C = 0.70       # 목표 PR 커버리지
M_REQ = 150             # κ₂ 추정에 필요한 Normative 유닛 수
N_MAIN = 100            # 본 실험 이슈 수
POOL_SIZE = 187         # 조건 통과 풀 (유한모집단 보정용)

C = {"reset": "\033[0m", "b": "\033[1m", "dim": "\033[2m",
     "g": "\033[32m", "y": "\033[33m", "r": "\033[31m", "c": "\033[36m"}


def col(s, *k):
    return "".join(C[x] for x in k) + str(s) + C["reset"]


# ── 통계 ─────────────────────────────────────────────────────

def fleiss_kappa(rows, cats):
    """rows: 항목별 라벨 리스트. 라벨러 수가 항목마다 같아야 한다.
    반환 (kappa, P_o, P_e, 주변분포)"""
    rows = [r for r in rows if len(r) >= 2]
    if not rows:
        return None
    k = len(rows[0])
    if any(len(r) != k for r in rows):
        return None
    N = len(rows)
    counts = [[r.count(c) for c in cats] for r in rows]
    # 항목별 일치 쌍 비율
    P_i = [(sum(n * n for n in row) - k) / (k * (k - 1)) for row in counts]
    P_o = sum(P_i) / N
    marg = [sum(row[j] for row in counts) / (N * k) for j in range(len(cats))]
    P_e = sum(p * p for p in marg)
    kappa = (P_o - P_e) / (1 - P_e) if P_e < 1 else None
    return kappa, P_o, P_e, dict(zip(cats, marg))


def gwet_ac1(rows, cats):
    """쏠린 분포에서 kappa 역설을 보완하는 지표.
    P_e 를 균등가정 쪽으로 잡아 prevalence 영향을 줄인다."""
    res = fleiss_kappa(rows, cats)
    if not res:
        return None
    _, P_o, _, marg = res
    q = len(cats)
    if q < 2:
        return None
    P_e = sum(p * (1 - p) for p in marg.values()) / (q - 1)
    return (P_o - P_e) / (1 - P_e) if P_e < 1 else None


def cohen_kappa(a, b, cats):
    n = len(a)
    if n == 0:
        return None
    P_o = sum(1 for x, y in zip(a, b) if x == y) / n
    P_e = sum((a.count(c) / n) * (b.count(c) / n) for c in cats)
    return (P_o - P_e) / (1 - P_e) if P_e < 1 else None


def wilson(k, n, z=1.96, N_pop=None):
    """이항비율 95% CI. N_pop 이 주어지면 유한모집단 보정."""
    if n == 0:
        return (None, None, None)
    p = k / n
    if N_pop and N_pop > n:
        z = z * math.sqrt((N_pop - n) / (N_pop - 1))
    d = 1 + z * z / n
    c = p + z * z / (2 * n)
    s = z * math.sqrt(p * (1 - p) / n + z * z / (4 * n * n))
    return (p, max(0.0, (c - s) / d), min(1.0, (c + s) / d))


def bootstrap_ci(by_issue, fn, reps, seed=20260906):
    """이슈 단위 복원추출. 유닛은 이슈 안에서 군집되므로
    유닛 단위로 뽑으면 CI 가 실제보다 좁게 나온다."""
    rng = random.Random(seed)
    keys = list(by_issue)
    if len(keys) < 2:
        return (None, None)
    vals = []
    for _ in range(reps):
        sample = [u for k in (rng.choice(keys) for _ in keys) for u in by_issue[k]]
        v = fn(sample)
        if v is not None:
            vals.append(v)
    if len(vals) < reps * 0.5:
        return (None, None)
    vals.sort()
    lo = vals[int(0.025 * len(vals))]
    hi = vals[min(int(0.975 * len(vals)), len(vals) - 1)]
    return (lo, hi)


# ── 로딩 ─────────────────────────────────────────────────────

def load(d):
    units = [json.loads(l) for l in (d / "units.jsonl").read_text(encoding="utf-8").splitlines() if l.strip()]
    labels = {}
    for f in sorted(d.glob("labels_*.jsonl")):
        who = f.stem.replace("labels_", "")
        rec = {}
        for line in f.read_text(encoding="utf-8").splitlines():
            if line.strip():
                r = json.loads(line)
                rec[r["sent_id"]] = r        # 같은 id 는 마지막 것이 유효
        labels[who] = rec
    return units, labels


def issue_meta(d):
    """이슈 라벨(bug / enhancement) — 분리 보고용"""
    out = {}
    skip = {"manifest.json", "attachments.json", "split_stats.json", "analysis.json"}
    for f in d.glob("*.json"):
        if f.name in skip:
            continue
        r = json.loads(f.read_text(encoding="utf-8"))
        tags = " ".join(r.get("labels", [])).lower()
        kind = ("bug" if ("bug" in tags or "defect" in tags)
                else "enhancement" if ("enhance" in tags or "feature" in tags)
                else "other")
        out[(r["repo"], r["number"])] = kind
    return out


# ── 본체 ─────────────────────────────────────────────────────

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--dir", required=True)
    ap.add_argument("--boot", type=int, default=2000)
    args = ap.parse_args()
    d = Path(args.dir)

    units, labels = load(d)
    who = sorted(labels)
    if not who:
        raise SystemExit(f"{d} 에 labels_*.jsonl 이 없습니다.")

    uidx = {u["sent_id"]: u for u in units}
    meta = issue_meta(d)
    out = {"n_labelers": len(who), "labelers": who, "M_all": len(units)}

    print("\n" + "=" * 72)
    print(col(f"  라벨링 집계 — {d}", "b"))
    print(f"  유닛 {len(units)}개 / 라벨러 {len(who)}명 ({', '.join(who)})")
    if len(who) < 3:
        print(col("  주의: 3인 미만입니다. κ 는 참고치로만 보세요.", "y"))
    print("=" * 72)

    # 완료율
    print(col("\n■ 완료 상태", "b"))
    for w in who:
        done = sum(1 for u in units if labels[w].get(u["sent_id"], {}).get("normative") is not None)
        mark = col("완료", "g") if done == len(units) else col(f"미완 {len(units)-done}건", "r")
        print(f"    {w}: {done}/{len(units)}  {mark}")
    complete = [w for w in who
                if all(labels[w].get(u["sent_id"], {}).get("normative") is not None for u in units)]
    if len(complete) < len(who):
        print(col("    → 미완료 라벨러는 일치도 계산에서 제외합니다.", "y"))
    who = complete
    if not who:
        raise SystemExit("완료된 라벨러가 없습니다.")

    # ── 1단계 ────────────────────────────────────────────────
    print(col("\n■ 1단계 — Normative / Descriptive", "b"))
    rows1, ids1 = [], []
    for u in units:
        r = [("N" if labels[w][u["sent_id"]]["normative"] else "D") for w in who]
        rows1.append(r)
        ids1.append(u["sent_id"])

    res1 = fleiss_kappa(rows1, ["N", "D"])
    if res1:
        k1, po1, pe1, marg1 = res1
        by_issue1 = defaultdict(list)
        for sid, r in zip(ids1, rows1):
            u = uidx[sid]
            by_issue1[(u["repo"], u["issue_number"])].append(r)
        lo, hi = bootstrap_ci(by_issue1,
                              lambda s: (fleiss_kappa(s, ["N", "D"]) or [None])[0], args.boot)
        ac1 = gwet_ac1(rows1, ["N", "D"])
        print(f"    Fleiss κ₁   {k1:.3f}   95% CI [{lo:.3f}, {hi:.3f}]" if lo is not None
              else f"    Fleiss κ₁   {k1:.3f}")
        print(f"    단순 일치율  {po1:.3f}      우연 기대 P_e {pe1:.3f}")
        print(f"    Gwet AC1    {ac1:.3f}" + col("   (쏠린 분포 보완 지표)", "dim"))
        print(f"    주변분포     N {marg1['N']:.1%} : D {marg1['D']:.1%}")
        if pe1 > 0.7:
            print(col("    ⚠ P_e 가 높습니다. 분포 쏠림으로 κ 가 낮게 나오는 구간입니다", "y"))
            print(col("      (kappa 역설). 일치율·AC1·주변분포를 함께 보고하세요.", "y"))
        gate1 = lo is not None and lo > KAPPA_GATE
        print(f"    게이트 {KAPPA_GATE}  →  " +
              (col("통과", "g") if gate1 else
               col("미달 — 가이드 개정 (표본 확대 아님)", "r") if (hi is not None and hi < KAPPA_GATE)
               else col("판정 유보 (CI 안에 게이트)", "y")))
        out["stage1"] = {"kappa": k1, "ci": [lo, hi], "P_o": po1, "P_e": pe1,
                         "ac1": ac1, "marginal": marg1}

    if len(who) > 1:
        print(col("    pairwise Cohen", "dim"))
        for a, b in combinations(range(len(who)), 2):
            ka = cohen_kappa([r[a] for r in rows1], [r[b] for r in rows1], ["N", "D"])
            print(f"      {who[a]}-{who[b]}: {ka:.3f}" if ka is not None else f"      {who[a]}-{who[b]}: n/a")

    # ── 2단계 — 교집합 ───────────────────────────────────────
    print(col("\n■ 2단계 — E / S / L  (3인 전원 Normative 교집합)", "b"))
    inter = [sid for sid, r in zip(ids1, rows1) if all(x == "N" for x in r)]
    rows2 = [[labels[w][s]["class"] for w in who] for s in inter]
    ok = [(s, r) for s, r in zip(inter, rows2) if all(x in ("E", "S", "L") for x in r)]
    inter, rows2 = [s for s, _ in ok], [r for _, r in ok]
    print(f"    교집합 유닛 {len(inter)}개")

    if len(inter) >= 5:
        res2 = fleiss_kappa(rows2, ["E", "S", "L"])
        k2, po2, pe2, marg2 = res2
        by_issue2 = defaultdict(list)
        for sid, r in zip(inter, rows2):
            u = uidx[sid]
            by_issue2[(u["repo"], u["issue_number"])].append(r)
        lo2, hi2 = bootstrap_ci(by_issue2,
                                lambda s: (fleiss_kappa(s, ["E", "S", "L"]) or [None])[0], args.boot)
        ac2 = gwet_ac1(rows2, ["E", "S", "L"])
        print(f"    Fleiss κ₂   {k2:.3f}" + (f"   95% CI [{lo2:.3f}, {hi2:.3f}]" if lo2 is not None else ""))
        print(f"    단순 일치율  {po2:.3f}      우연 기대 P_e {pe2:.3f}")
        print(f"    Gwet AC1    {ac2:.3f}")
        print("    주변분포     " + "  ".join(f"{k} {v:.1%}" for k, v in marg2.items()))
        gate2 = lo2 is not None and lo2 > KAPPA_GATE
        print(f"    게이트 {KAPPA_GATE}  →  " +
              (col("통과", "g") if gate2 else
               col("미달 — 가이드 개정", "r") if (hi2 is not None and hi2 < KAPPA_GATE)
               else col("판정 유보", "y")))
        out["stage2"] = {"kappa": k2, "ci": [lo2, hi2], "P_o": po2, "P_e": pe2,
                         "ac1": ac2, "marginal": marg2, "n_intersection": len(inter)}
        if len(who) > 1:
            print(col("    pairwise Cohen", "dim"))
            for a, b in combinations(range(len(who)), 2):
                ka = cohen_kappa([r[a] for r in rows2], [r[b] for r in rows2], ["E", "S", "L"])
                print(f"      {who[a]}-{who[b]}: {ka:.3f}" if ka is not None else f"      {who[a]}-{who[b]}: n/a")
    else:
        print(col("    교집합이 너무 작아 κ₂ 를 계산하지 않습니다.", "y"))
        out["stage2"] = {"n_intersection": len(inter)}

    # ── 분포와 파라미터 ──────────────────────────────────────
    print(col("\n■ 분포", "b"))
    n_iss = len({(u["repo"], u["issue_number"]) for u in units})
    m_norm_int = len([s for s, r in zip(ids1, rows1) if all(x == "N" for x in r)]) / n_iss
    per_person = [sum(1 for s in ids1 if labels[w][s]["normative"]) / n_iss for w in who]
    m_norm_ind = sum(per_person) / len(per_person)
    gap = (m_norm_ind - m_norm_int) / m_norm_ind * 100 if m_norm_ind else 0
    print(f"    m̄_all        {len(units)/n_iss:.1f}")
    print(f"    개인 m̄_norm   {m_norm_ind:.2f}   " + col("(참고값)", "dim"))
    print(f"    교집합 m̄_norm {m_norm_int:.2f}   " + col(f"격차 {gap:.0f}%", "dim"))

    # 합의 라벨 — 다수결
    consensus = {}
    for s, r in zip(inter, rows2):
        c = Counter(r).most_common()
        consensus[s] = c[0][0] if (len(c) == 1 or c[0][1] > c[1][1]) else None
    dist = Counter(v for v in consensus.values() if v)
    total = sum(dist.values())
    if total:
        print("    E/S/L 합의   " + "  ".join(f"{k} {dist[k]}({dist[k]/total:.1%})" for k in "ESL"))

    # 이슈 단위 E 비율 — 주 지표
    e_iss = {(uidx[s]["repo"], uidx[s]["issue_number"]) for s, v in consensus.items() if v == "E"}
    p, lo3, hi3 = wilson(len(e_iss), n_iss)
    print(col("\n■ 주 지표 — 이슈 단위 E 비율", "b"))
    print(f"    {len(e_iss)}/{n_iss} = {p:.1%}   95% CI [{lo3:.1%}, {hi3:.1%}]")
    print(col(f"    (사전 측정 {n_iss}건 기준이므로 CI 가 매우 넓습니다. 본 실험에서 확정)", "dim"))

    # bug / enhancement 분리
    kinds = defaultdict(lambda: [0, 0])
    for k in {(u["repo"], u["issue_number"]) for u in units}:
        kinds[meta.get(k, "other")][1] += 1
        if k in e_iss:
            kinds[meta.get(k, "other")][0] += 1
    print("    유형별       " + "  ".join(f"{k} {a}/{b}" for k, (a, b) in sorted(kinds.items())))

    # 파라미터
    print(col("\n■ 본 실험 파라미터", "b"))
    if m_norm_int > 0:
        n_ov = math.ceil(M_REQ / m_norm_int)
        p_star = 1 - (1 - COVERAGE_C) ** (1 / m_norm_int)
        print(f"    n_ov = ceil({M_REQ} / {m_norm_int:.2f}) = {n_ov}")
        if n_ov > N_MAIN:
            print(col(f"    ⚠ 상한 {N_MAIN} 초과. 100건 전부를 3인 중복해도", "r"))
            print(col(f"      Normative 유닛이 약 {m_norm_int*N_MAIN:.0f}개로 {M_REQ}에 미달합니다.", "r"))
            print(col("      → 이슈 추가 수집 / M_req 하향 / κ 를 보조 지표로 강등 중 택일", "y"))
            n_ov = N_MAIN
        print(f"    p*   = 1 - (1-{COVERAGE_C})^(1/{m_norm_int:.2f}) = {p_star:.1%}")
        est_units = (n_ov * len(who) + (N_MAIN - n_ov)) * (len(units) / n_iss)
        print(f"    예상 작업량   총 {est_units:.0f} 유닛-라벨 / 1인당 {est_units/max(len(who),1)/450:.1f}시간 (8초 기준)")
        out["params"] = {"m_norm_intersection": m_norm_int, "m_norm_individual": m_norm_ind,
                         "n_ov": n_ov, "p_star": p_star,
                         "issue_E_ratio": p, "issue_E_ci": [lo3, hi3]}

    # 소요 시간
    print(col("\n■ 소요 시간", "b"))
    for w in who:
        ts = sorted(datetime.fromisoformat(r["ts"]) for r in labels[w].values() if r.get("ts"))
        g = sorted((b - a).total_seconds() for a, b in zip(ts, ts[1:]) if (b - a).total_seconds() < 300)
        if g:
            print(f"    {w}: 중앙값 {g[len(g)//2]:.0f}초/유닛, 총 {sum(g)/60:.0f}분")

    # ── 불일치 목록 ──────────────────────────────────────────
    dis = []
    for s, r in zip(ids1, rows1):
        if len(set(r)) > 1:
            dis.append(("1단계", s, dict(zip(who, r))))
    for s, r in zip(inter, rows2):
        if len(set(r)) > 1:
            dis.append(("2단계", s, dict(zip(who, r))))

    lines = ["# 불일치 유닛 — 회의 안건", "",
             f"1단계 {sum(1 for x in dis if x[0]=='1단계')}건 / "
             f"2단계 {sum(1 for x in dis if x[0]=='2단계')}건", "",
             "합의 라벨은 실험 B 정답용으로만 쓴다. **κ 는 합의 전 원본 라벨로 계산한다.**", ""]
    for stage, s, r in dis:
        u = uidx[s]
        lines.append(f"- `{s}` ({stage}) " + " / ".join(f"{k}:{v}" for k, v in r.items()))
        lines.append(f"    {u['text'][:140]}")
    (d / "disagreements.md").write_text("\n".join(lines), encoding="utf-8")

    out["disagreements"] = {"stage1": sum(1 for x in dis if x[0] == "1단계"),
                            "stage2": sum(1 for x in dis if x[0] == "2단계")}
    (d / "analysis.json").write_text(json.dumps(out, ensure_ascii=False, indent=1), encoding="utf-8")

    print(col("\n■ 산출물", "b"))
    print(f"    {d/'analysis.json'}")
    print(f"    {d/'disagreements.md'}   불일치 1단계 {out['disagreements']['stage1']}건 / "
          f"2단계 {out['disagreements']['stage2']}건")
    print("=" * 72 + "\n")


if __name__ == "__main__":
    main()
