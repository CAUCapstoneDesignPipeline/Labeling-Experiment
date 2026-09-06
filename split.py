#!/usr/bin/env python3
"""
split.py — 이슈 텍스트를 라벨링 유닛으로 분리  (v2)

collect_issues.py가 만든 이슈 JSON을 읽어 유닛 단위로 쪼갠다.
3인이 이 결과를 그대로 공유하고 라벨만 붙인다.
분리 결과가 라벨러마다 다르면 일치도 계산이 불가능하므로, 이 스크립트는
한 번만 돌리고 결과를 고정한다.

이 모듈은 실험 전용이 아니라 파이프라인이 그대로 쓸 모듈이다.

v2 변경 (1차 검수 반영):
  1. HTML 태그 제거 — 붙여넣은 서식 텍스트가 유닛을 오염시키던 문제
  2. `**Expected:**` 등 볼드/밑줄 헤더를 블록 경계로 인식
     (앞 문장 끝에 붙어 기대 동작 구간 경계가 사라지던 문제)
  3. merged_short가 코멘트 경계를 넘지 않도록 차단
  4. 템플릿 잔재 제거 — _No response_, 체크박스, 알림 메일 답장, 버전 필드
  5. 인용 블록 중복 제거 — 같은 이슈에 원본이 있으면 제외, 없으면 유지

사용:
  python split.py --dir data/exp0
  python split.py --dir data/main

출력:
  <dir>/units.jsonl        유닛 (라벨러 배포용)
  <dir>/attachments.json   코드 블록 원문
  <dir>/review.md          눈으로 검수할 사람용 파일
  <dir>/split_stats.json   집계
"""

import argparse
import html
import json
import re
from collections import Counter
from pathlib import Path

MIN_WORDS = 3          # 이보다 짧은 유닛은 직전 유닛에 병합 (같은 세그먼트 안에서만)

ABBREV = {
    "e.g", "i.e", "vs", "etc", "cf", "resp", "approx", "fig", "no", "ex",
    "al", "dr", "mr", "ms", "st", "vol", "sec", "ch", "eq", "inc", "ltd",
    "jr", "sr", "pp", "ed", "est", "min", "max", "avg",
}

# 이슈 템플릿이 남기는 무의미한 줄
TEMPLATE_NOISE = [
    re.compile(r"^_?no response_?$", re.I),
    re.compile(r"^n/?a$", re.I),
    re.compile(r"^-?\s*\[[ xX]\]\s*I (agree|can reproduce|have searched|checked)", re.I),
    re.compile(r"^-?\s*\[[ xX]\]\s*$"),
]

# HTML 태그 — 태그명을 명시한다. `<[^<>]*>` 로 뭉뚱그리면
# 코드 밖에 쓰인 Java 제네릭(<Buffer>, <String>)까지 지워진다.
HTML_TAG = re.compile(
    r"<\s*/?\s*(?:a|abbr|b|blockquote|br|center|code|del|details|div|em|font|"
    r"h[1-6]|hr|i|img|ins|kbd|li|ol|p|pre|s|samp|small|span|strong|sub|summary|"
    r"sup|table|tbody|td|tfoot|th|thead|tr|u|ul|var)\b[^<>]*>",
    re.I,
)

# GitHub 알림 메일로 답장했을 때 딸려오는 보일러플레이트
EMAIL_NOISE = [
    re.compile(r"^On .{0,80}wrote:\s*$", re.I),
    re.compile(r"you are receiving this because", re.I),
    re.compile(r"reply to this email directly", re.I),
    re.compile(r"view it on github", re.I),
    re.compile(r"\bunsubscribe\b", re.I),
    re.compile(r"^\*\*\*@\*\*\*", re.I),
    re.compile(r"^-{2,}\s*$"),
]

# 버전만 적힌 템플릿 필드 (예: "4.3.4-SNAPSHOT", "4.4.1, 4.5.31")
RE_VERSION_ONLY = re.compile(
    r"^⟦V:\d+⟧[-\w.]*(?:\s*,\s*⟦V:\d+⟧[-\w.]*)*\.?$"
)

# 볼드/밑줄 헤더 — 마크다운 헤딩이 아니라 서식으로 쓰인 구획 표시
HEADER_WORDS = (
    r"expected(?:\s+(?:behaviou?rs?|results?|output))?|"
    r"actual(?:\s+(?:behaviou?rs?|results?|output))?|"
    r"current(?:\s+behaviou?rs?)?|"
    r"steps?\s+to\s+reproduce|reproduction\s+steps?|reproducer|"
    r"description|context|environment|versions?|"
    r"additional\s+(?:context|information)|workaround|"
    r"observed(?:\s+behaviou?rs?)?|desired(?:\s+behaviou?rs?)?|"
    r"probable\s+cause"
)
# 줄 전체가 헤더인 경우: **Expected:**, __Actual__, Expected behavior
RE_HEADER_LINE = re.compile(
    rf"^\s*(?:\*\*|__)?\s*(?:{HEADER_WORDS})\s*:?\s*(?:\*\*|__)?\s*:?\s*$", re.I
)
# 문장 꼬리에 붙은 헤더: "... can be reused Actual:" → 잘라낸다
RE_HEADER_TAIL = re.compile(
    rf"\s+(?:\*\*|__)?((?:{HEADER_WORDS}))\s*:?\s*(?:\*\*|__)?\s*$", re.I
)


# ─────────────────────────────────────────────────────────────
# 1. 전처리 — 삭제하지 않고 토큰으로 치환
#    삭제하면 문장 구조가 깨진다
# ─────────────────────────────────────────────────────────────

class Protector:
    def __init__(self):
        self.code = []      # 펜스 코드 블록 / 스택 트레이스
        self.inline = []    # 인라인 코드
        self.ver = []       # 버전 번호

    def protect(self, text):
        if not text:
            return ""
        t = text.replace("\r\n", "\n")

        # 펜스 코드 블록 (스택 트레이스 대부분이 여기 들어 있음)
        def _fence(m):
            self.code.append(m.group(0))
            return f"\n⟦CODE:{len(self.code)-1}⟧\n"
        t = re.sub(r"```.*?```", _fence, t, flags=re.S)
        t = re.sub(r"~~~.*?~~~", _fence, t, flags=re.S)

        # 펜스 밖 스택 트레이스 (`at com.foo.Bar(...)` 연속 줄)
        def _trace(m):
            self.code.append(m.group(0))
            return f"\n⟦CODE:{len(self.code)-1}⟧\n"
        t = re.sub(r"(?:^[ \t]*at [\w.$<>]+\(.*\)\s*$\n?){2,}",
                   _trace, t, flags=re.M)

        # 인라인 코드를 HTML보다 먼저 보호한다.
        # 순서를 바꾸면 `Supplier<SslContextFactory>` 같은 Java 제네릭이
        # HTML 태그로 오인되어 잘려나간다.
        def _inline(m):
            self.inline.append(m.group(1))
            return f"⟦C:{len(self.inline)-1}⟧"
        t = re.sub(r"`([^`\n]+)`", _inline, t)

        # ── HTML 처리 (v2) ──
        # 붙여넣은 서식 텍스트가 인라인 CSS 수천 자를 끌고 들어온다.
        # 태그명을 명시해 코드 밖의 제네릭(<Buffer> 등)까지 지우지 않도록 한다.
        t = re.sub(r"<!--.*?-->", "", t, flags=re.S)
        t = re.sub(r"<(script|style)\b.*?</\1>", "", t, flags=re.S | re.I)
        t = re.sub(r"<(?:br|hr)\s*/?>", "\n", t, flags=re.I)
        t = re.sub(r"</(?:p|div|li|ul|ol|h[1-6]|tr|table|blockquote|details)\s*>",
                   "\n", t, flags=re.I)
        t = re.sub(r"<li\b[^<>]*>", "\n- ", t, flags=re.I)
        t = re.sub(r"<t[dh]\b[^<>]*>", " | ", t, flags=re.I)
        t = HTML_TAG.sub("", t)
        t = html.unescape(t)

        # 마크다운 강조 표시 제거 (내용은 그대로)
        t = re.sub(r"\*\*(.+?)\*\*", r"\1", t, flags=re.S)
        t = re.sub(r"__(.+?)__", r"\1", t, flags=re.S)

        # 이미지 제거, 링크는 표시 텍스트만
        t = re.sub(r"!\[[^\]]*\]\([^)]*\)", "", t)
        t = re.sub(r"\[([^\]]+)\]\([^)]*\)", r"\1", t)
        t = re.sub(r"https?://\S+", "⟦URL⟧", t)

        # 버전 번호 — 마침표에서 잘리는 것을 막는다
        def _ver(m):
            self.ver.append(m.group(0))
            return f"⟦V:{len(self.ver)-1}⟧"
        t = re.sub(r"\b\d+\.\d+(?:\.\d+)*\b", _ver, t)

        return t

    def restore(self, text):
        """인라인 코드와 버전은 되살린다 (문장의 일부라 가독성에 필요).
        코드 블록은 첨부로 분리하므로 되살리지 않는다."""
        def _i(m):
            return f"`{self.inline[int(m.group(1))]}`"
        def _v(m):
            return self.ver[int(m.group(1))]
        text = re.sub(r"⟦C:(\d+)⟧", _i, text)
        text = re.sub(r"⟦V:(\d+)⟧", _v, text)
        return text


# ─────────────────────────────────────────────────────────────
# 2. 문장 분리 (산문 문단에만 적용)
# ─────────────────────────────────────────────────────────────

SENT_BOUNDARY = re.compile(
    r"(?:(?<=[.!?])|(?<=[.!?][)\"'\]]))\s+(?=[A-Z⟦\"'(\[])"
)


def _ends_with_abbrev(s):
    m = re.search(r"([A-Za-z.]+)\.$", s.strip())
    return bool(m) and m.group(1).lower().rstrip(".") in ABBREV


def split_sentences(text):
    parts = [p for p in SENT_BOUNDARY.split(text) if p.strip()]
    out = []
    for p in parts:
        if out and _ends_with_abbrev(out[-1]):
            out[-1] = out[-1] + " " + p
        else:
            out.append(p)
    return [s.strip() for s in out if s.strip()]


# ─────────────────────────────────────────────────────────────
# 3. 블록 분해
# ─────────────────────────────────────────────────────────────

RE_HEADING = re.compile(r"^\s{0,3}#{1,6}\s+")
RE_BULLET = re.compile(r"^(\s*)(?:[-*+]|\d+[.)])\s+(.*)$")
RE_QUOTE = re.compile(r"^\s*>\s?(.*)$")
RE_TABLE_SEP = re.compile(r"^\s*\|?[\s:|-]+\|[\s:|-]*$")
RE_TABLE_ROW = re.compile(r"^\s*\|.*\|\s*$")
RE_CODE_TOKEN = re.compile(r"^\s*⟦CODE:(\d+)⟧\s*$")
RE_HRULE = re.compile(r"^\s*([-*_])\1{2,}\s*$")


def is_noise_line(line):
    s = line.strip()
    if not s:
        return False
    for p in TEMPLATE_NOISE:
        if p.match(s):
            return True
    for p in EMAIL_NOISE:
        if p.search(s):
            return True
    return False


def strip_header_tail(text):
    """문장 꼬리에 붙은 'Actual:' 같은 헤더를 잘라낸다."""
    m = RE_HEADER_TAIL.search(text)
    if m and len(text[:m.start()].split()) >= MIN_WORDS:
        return text[:m.start()].rstrip()
    return text


def blocks_to_units(text):
    """(block_type, raw_text) 리스트. 코드 토큰은 그대로 흘려보낸다."""
    units, para, quote = [], [], []

    def emit(bt, s):
        s = s.strip()
        if not s or is_noise_line(s):
            return
        # 문장부호만 남은 조각 (링크 제거 후 남는 ". " 등)
        if not re.search(r"\w", re.sub(r"⟦[^⟧]*⟧", "", s)):
            return
        # 줄 전체가 헤더면 유닛으로 만들지 않는다 (구획 표시일 뿐)
        if RE_HEADER_LINE.match(s):
            return
        if RE_VERSION_ONLY.match(s):
            return
        s = strip_header_tail(s)
        if s.strip():
            units.append((bt, s.strip()))

    def flush_quote():
        # 인용은 블록 단위로 모아서 문장 분리한다.
        # 줄 단위로 쪼개면 원본과 텍스트가 달라져 중복 판정이 실패한다.
        if quote:
            joined = " ".join(quote).strip()
            for s in split_sentences(joined):
                emit("quote", s)
            quote.clear()

    def flush_para():
        flush_quote()
        if para:
            joined = " ".join(para).strip()
            for s in split_sentences(joined):
                emit("para", s)
            para.clear()

    for line in text.split("\n"):
        if not line.strip():
            flush_para()
            continue

        if is_noise_line(line):
            flush_para()
            continue

        m = RE_CODE_TOKEN.match(line)
        if m:
            flush_para()
            units.append(("__code__", line.strip()))
            continue

        if RE_HEADING.match(line) or RE_HRULE.match(line):
            # 본문 안의 마크다운 헤딩은 템플릿 구조 — 유닛이 아니다
            flush_para()
            continue

        # 볼드/밑줄 헤더도 블록 경계로 취급 (v2)
        if RE_HEADER_LINE.match(line):
            flush_para()
            continue

        m = RE_BULLET.match(line)
        if m:
            flush_para()
            emit("bullet", m.group(2))
            continue

        m = RE_QUOTE.match(line)
        if m:
            if para:
                flush_para()
            if m.group(1).strip():
                quote.append(m.group(1).strip())
            continue
        flush_quote()

        if RE_TABLE_SEP.match(line):
            continue
        if RE_TABLE_ROW.match(line):
            flush_para()
            cells = [c.strip() for c in line.strip().strip("|").split("|")]
            emit("table", " | ".join(c for c in cells if c))
            continue

        # 불릿 항목의 이어지는 줄이면 직전 유닛에 붙인다
        if units and units[-1][0] == "bullet" and line.startswith((" ", "\t")) and not para:
            units[-1] = ("bullet", units[-1][1] + " " + line.strip())
            continue

        para.append(line.strip())

    flush_para()
    return units


# ─────────────────────────────────────────────────────────────
# 4. 이슈 하나 처리
# ─────────────────────────────────────────────────────────────

def word_count(s):
    return len(re.findall(r"\S+", s))


def is_placeholder_only(s):
    return not re.sub(r"⟦[^⟧]*⟧", "", s).strip()


def norm_for_dedup(s):
    """인용 중복 판정용 정규화 — 플레이스홀더·구두점·대소문자 무시"""
    s = re.sub(r"⟦[^⟧]*⟧", " ", s)
    s = re.sub(r"[^\w\s]", " ", s.lower())
    return re.sub(r"\s+", " ", s).strip()


def process_issue(rec):
    p = Protector()
    slug = rec["repo"].split("/")[1]
    raw = []   # (source, seg, block_type, text)
    #  seg: 제목=-1, 본문=0, 코멘트=1,2,3...   병합이 이 경계를 넘지 않는다

    # 이슈 제목은 유닛에 포함한다.
    # 요구사항이 제목에만 압축되어 있는 경우가 많아, 빼면 과소 측정된다.
    raw.append(("title", -1, "title", p.protect(rec["title"])))

    for bt, t in blocks_to_units(p.protect(rec["body"] or "")):
        raw.append(("body", 0, bt, t))

    for ci, c in enumerate(rec.get("comments", []), 1):
        for bt, t in blocks_to_units(p.protect(c["body"] or "")):
            raw.append(("comment", ci, bt, t))

    units, stats = [], Counter()
    for source, seg, bt, text in raw:
        text = text.strip()
        if not text:
            continue

        # 코드 블록 단독 줄 → 직전 유닛의 첨부로
        m = RE_CODE_TOKEN.match(text)
        if m:
            if units:
                units[-1]["attachments"].append(int(m.group(1)))
                stats["attached_to_prev"] += 1
            else:
                stats["orphan_code"] += 1
            continue

        # 문장 안에 섞인 코드 토큰 → 첨부로 떼고 텍스트에서 제거
        inline_codes = [int(x) for x in re.findall(r"⟦CODE:(\d+)⟧", text)]
        text = re.sub(r"⟦CODE:\d+⟧", "", text).strip()

        if is_placeholder_only(text) or not text:
            stats["dropped_placeholder_only"] += 1
            continue

        # 너무 짧은 유닛은 직전에 병합 — 단 같은 세그먼트 안에서만 (v2)
        if word_count(text) < MIN_WORDS:
            if units and units[-1]["_seg"] == seg:
                units[-1]["text"] += " " + p.restore(text)
                units[-1]["attachments"] += inline_codes
                stats["merged_short"] += 1
            else:
                stats["dropped_short_at_boundary"] += 1
            continue

        units.append({
            "source": source,
            "_seg": seg,
            "block_type": bt,
            "text": p.restore(text),
            "attachments": inline_codes,
        })

    # 인용 중복 제거 (v2)
    # 같은 이슈에 원본이 있으면 제외, 없으면 유지 —
    # 외부 문서·javadoc 인용은 Normative일 수 있다.
    non_quote = [norm_for_dedup(u["text"])
                 for u in units if u["block_type"] != "quote"]
    kept = []
    for u in units:
        if u["block_type"] == "quote":
            key = norm_for_dedup(u["text"])
            # 완전 일치뿐 아니라 부분 인용도 중복으로 본다
            dup = (not key) or any(
                key == o or (len(key) >= 12 and key in o) for o in non_quote)
            if dup:
                stats["dropped_quote_duplicate"] += 1
                continue
            stats["kept_quote_original"] += 1
        kept.append(u)
    units = kept

    for i, u in enumerate(units, 1):
        u.pop("_seg", None)
        u["sent_id"] = f"{slug}-{rec['number']}-{i:03d}"
        u["repo"] = rec["repo"]
        u["issue_number"] = rec["number"]
        u["attachments"] = [p.code[j] for j in u["attachments"]]
        stats[f"block:{u['block_type']}"] += 1
        stats[f"source:{u['source']}"] += 1

    return units, stats


# ─────────────────────────────────────────────────────────────
# 5. 실행
# ─────────────────────────────────────────────────────────────

FIELD_ORDER = ["sent_id", "repo", "issue_number", "source",
               "block_type", "text", "attachments"]


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--dir", required=True, help="예: data/exp0")
    args = ap.parse_args()

    d = Path(args.dir)
    # 자기 출력 파일을 다시 입력으로 읽지 않도록 제외 (재실행 대비)
    skip = {"manifest.json", "attachments.json", "split_stats.json"}
    files = sorted(f for f in d.glob("*.json") if f.name not in skip)
    if not files:
        raise SystemExit(f"{d}에 이슈 JSON이 없습니다. collect_issues.py를 먼저 실행하세요.")

    all_units, total = [], Counter()
    per_issue, attachments = {}, {}

    for f in files:
        rec = json.loads(f.read_text(encoding="utf-8"))
        units, stats = process_issue(rec)
        all_units += units
        total.update(stats)
        per_issue[f"{rec['repo']}#{rec['number']}"] = len(units)
        for u in units:
            if u["attachments"]:
                attachments[u["sent_id"]] = u["attachments"]

    # units.jsonl — 라벨러 배포용
    with (d / "units.jsonl").open("w", encoding="utf-8") as fh:
        for u in all_units:
            row = {k: u[k] for k in FIELD_ORDER}
            fh.write(json.dumps(row, ensure_ascii=False) + "\n")

    (d / "attachments.json").write_text(
        json.dumps(attachments, ensure_ascii=False, indent=1), encoding="utf-8")

    # review.md — 눈으로 검수할 파일
    lines = ["# 분리 결과 검수", "",
             "각 유닛이 요구 하나에 대응하는지 확인한다.", "",
             "```", "□ 불릿이 항목별로 쪼개졌는가",
             "□ 코드 안의 마침표에서 잘리지 않았는가",
             "□ 버전 번호에서 잘리지 않았는가",
             "□ 축약어(e.g., i.e.)에서 잘리지 않았는가",
             "□ 한 유닛에 독립된 요구가 2개 이상 들어 있지 않은가",
             "□ 스택 트레이스가 유닛으로 잡히지 않았는가",
             "□ HTML 태그·CSS가 남아 있지 않은가",
             "□ Expected/Actual 헤더가 앞 문장 끝에 붙어 있지 않은가",
             "□ 다른 사람의 코멘트가 앞 유닛에 병합되지 않았는가", "```", ""]
    cur = None
    for u in all_units:
        key = f"{u['repo']}#{u['issue_number']}"
        if key != cur:
            cur = key
            lines += ["", f"## {key}", ""]
        att = f"  [+{len(u['attachments'])} code]" if u["attachments"] else ""
        lines.append(f"- `{u['sent_id']}` "
                     f"({u['source']}/{u['block_type']}){att}  {u['text']}")
    (d / "review.md").write_text("\n".join(lines), encoding="utf-8")

    counts = sorted(per_issue.values())
    n = len(per_issue)
    stats_out = {
        "n_issues": n,
        "M_all": len(all_units),
        "m_bar_all": round(len(all_units) / n, 2),
        "min_units_per_issue": counts[0],
        "median_units_per_issue": counts[n // 2],
        "max_units_per_issue": counts[-1],
        "detail": dict(total),
        "per_issue": per_issue,
    }
    (d / "split_stats.json").write_text(
        json.dumps(stats_out, ensure_ascii=False, indent=1), encoding="utf-8")

    print(f"이슈 {n}건 → 유닛 {len(all_units)}개 (이슈당 평균 {stats_out['m_bar_all']})")
    print(f"  최소 {counts[0]} / 중앙 {counts[n//2]} / 최대 {counts[-1]}")
    for k in sorted(total):
        print(f"  {k}: {total[k]}")
    print(f"\n다음: {d/'review.md'} 를 눈으로 검수하세요.")
    print("규칙을 고치면 이 스크립트를 다시 돌려 전체를 재분리합니다.")


if __name__ == "__main__":
    main()
