#!/usr/bin/env python3
"""
label.py — 라벨링 CLI

units.jsonl을 한 유닛씩 보여주고 키 입력으로 라벨을 받는다.
라벨은 라벨러별 파일에 저장되며, 언제든 중단하고 다시 이어서 할 수 있다.

사용:
  python3 label.py --dir data/exp0 --labeler A
  python3 label.py --dir data/exp0 --labeler A --review    # 붙인 라벨 다시 보기
  python3 label.py --dir data/exp0 --labeler A --goto 42   # 특정 번호부터

저장 위치:
  <dir>/labels_<labeler>.jsonl

주의:
  - 라벨링 중 팀원과 상의하지 않는다. 독립성이 깨지면 일치도 측정이 무의미해진다.
  - 전원이 끝나기 전에는 서로의 라벨 파일을 보지 않는다.
  - 판단이 서지 않으면 낮은 쪽으로 내리고 note에 사유를 적는다.
"""

import argparse
import json
import os
import re
import shutil
import sys
import time
from pathlib import Path

# ─────────────────────────────────────────────────────────────

C = {
    "reset": "\033[0m", "dim": "\033[2m", "bold": "\033[1m",
    "cyan": "\033[36m", "yellow": "\033[33m", "green": "\033[32m",
    "red": "\033[31m", "blue": "\033[34m", "mag": "\033[35m",
}
if not sys.stdout.isatty() or os.environ.get("NO_COLOR"):
    C = {k: "" for k in C}


def c(s, *styles):
    return "".join(C[x] for x in styles) + str(s) + C["reset"]


def width():
    return min(shutil.get_terminal_size((90, 24)).columns, 100)


def wrap(text, indent=2):
    """터미널 폭에 맞춰 줄바꿈. 단어 단위."""
    w = width() - indent
    out, line = [], ""
    for word in text.split():
        if len(line) + len(word) + 1 > w:
            out.append(line)
            line = word
        else:
            line = f"{line} {word}".strip()
    if line:
        out.append(line)
    return "\n".join(" " * indent + l for l in out)


def rule(ch="─"):
    return c(ch * width(), "dim")


# ─────────────────────────────────────────────────────────────
# 입출력
# ─────────────────────────────────────────────────────────────

def load_units(d):
    p = d / "units.jsonl"
    if not p.exists():
        sys.exit(f"{p} 가 없습니다. split.py를 먼저 실행하세요.")
    return [json.loads(l) for l in p.read_text(encoding="utf-8").splitlines() if l.strip()]


def load_attachments(d):
    p = d / "attachments.json"
    return json.loads(p.read_text(encoding="utf-8")) if p.exists() else {}


def load_labels(path):
    """같은 sent_id가 여러 번 있으면 마지막 것이 유효 (수정 이력 보존)."""
    if not path.exists():
        return {}
    out = {}
    for line in path.read_text(encoding="utf-8").splitlines():
        if line.strip():
            r = json.loads(line)
            out[r["sent_id"]] = r
    return out


def append_label(path, rec):
    with path.open("a", encoding="utf-8") as fh:
        fh.write(json.dumps(rec, ensure_ascii=False) + "\n")
        fh.flush()
        os.fsync(fh.fileno())


# ─────────────────────────────────────────────────────────────
# 화면
# ─────────────────────────────────────────────────────────────

GUIDES = {
    "1": ("LABELING_GUIDE_SENTENCE.md", "1단계 — Normative / Descriptive"),
    "2": ("LABELING_GUIDE_ESL.md", "2단계 — E / S / L"),
}


def find_guide(fname, d):
    """가이드 파일 위치 — 저장소 루트 우선, 없으면 데이터 폴더·스크립트 옆."""
    for base in (Path.cwd(), d, d.parent, d.parent.parent,
                 Path(__file__).resolve().parent):
        p = base / fname
        if p.exists():
            return p
    return None


def guide_sections(path):
    """## / ### 헤딩 단위로 잘라 {번호: (제목, 본문)} 로 만든다.
    가이드 파일이 곧 기준이므로, 도움말을 코드에 복사해두지 않는다."""
    text = path.read_text(encoding="utf-8")
    secs, cur, buf = [], None, []
    for line in text.splitlines():
        if line.startswith("## "):
            if cur:
                secs.append((cur, "\n".join(buf).strip()))
            cur, buf = line[3:].strip(), []
        elif cur is not None:
            buf.append(line)
    if cur:
        secs.append((cur, "\n".join(buf).strip()))
    out = {}
    for title, body in secs:
        m = re.match(r"^(\d+)\.\s*(.*)$", title)
        key = m.group(1) if m else title
        out[key] = (m.group(2) if m else title, body)
    return out


def render_md(body):
    """터미널용 최소 렌더링 — 강조 제거, 헤딩·코드블록·표를 눈에 띄게."""
    lines, in_code = [], False
    for raw in body.splitlines():
        line = raw
        if line.strip().startswith("```"):
            in_code = not in_code
            continue
        if in_code:
            lines.append(c("  │ " + line, "dim"))
            continue
        if line.startswith("### "):
            lines.append("")
            lines.append(c("  " + line[4:], "bold", "cyan"))
            continue
        line = re.sub(r"\*\*(.+?)\*\*", lambda m: c(m.group(1), "bold"), line)
        line = line.replace("**", "")      # 줄바꿈에 걸친 강조 잔재
        line = re.sub(r"`([^`]+)`", lambda m: c(m.group(1), "yellow"), line)
        if line.strip().startswith("|"):
            lines.append("  " + line.strip())
        elif line.strip():
            lines.append(wrap(line.strip()) if len(line) > width() - 2
                         else "  " + line.strip())
        else:
            lines.append("")
    return "\n".join(lines)


def show_guide(d, which=None, sec=None):
    if which is None:
        print(c("\n  ? 뒤에 번호를 붙여 가이드를 엽니다", "bold"))
        print("   ?1        1단계 가이드 목차      ?2        2단계 가이드 목차")
        print("   ?1.4      1단계 §4 경계 사례     ?2.6      2단계 §6 경계 사례")
        print("   ?1.5      1단계 §5 지킬 규칙     ?2.7      2단계 §7 지킬 규칙")
        print(c(KEYS, "dim"))
        return
    fname, label = GUIDES[which]
    path = find_guide(fname, d)
    if not path:
        print(c(f"  {fname} 를 찾을 수 없습니다. 저장소 루트에서 실행하세요.", "red"))
        return
    secs = guide_sections(path)
    if sec is None:
        print(c(f"\n  {label}  ({path})", "bold"))
        for k, (title, _) in secs.items():
            print(f"   ?{which}.{k:<3} {title}")
        return
    if sec not in secs:
        print(c(f"  §{sec} 없음. ?{which} 로 목차를 보세요.", "red"))
        return
    title, body = secs[sec]
    print("\n" + rule("═"))
    print(c(f"  {label} — §{sec} {title}", "bold"))
    print(rule())
    print(render_md(body))
    print(rule("═"))


KEYS = """
  1단계   n Normative      d Descriptive
  2단계   e Executable     s Structural     l LLM 판정만
  그 외   a 첨부 코드      b 이전 유닛      t note
          g 번호 이동      p 진행 상황      ? 가이드       q 저장 후 종료
"""


def show_unit(u, idx, total, done, existing):
    print("\n" + rule("═"))
    pct = done * 100 // total if total else 0
    bar_w = 24
    filled = int(bar_w * done / total) if total else 0
    bar = c("█" * filled, "green") + c("░" * (bar_w - filled), "dim")
    print(f"  {c(f'[{idx+1}/{total}]', 'bold')}  {bar} {done}/{total} ({pct}%)")
    print(f"  {c(u['sent_id'], 'cyan')}   "
          f"{c(u['repo'] + '#' + str(u['issue_number']), 'dim')}   "
          f"{c(u['source'] + '/' + u['block_type'], 'dim')}"
          + (c(f"   [+{len(u['attachments'])} code — a키]", 'mag')
             if u.get("attachments") else ""))
    print(rule())
    print()
    print(wrap(u["text"]))
    print()
    if existing:
        cls = existing.get("class") or "-"
        tag = "Normative" if existing["normative"] else "Descriptive"
        note = f"  note: {existing['note']}" if existing.get("note") else ""
        print(c(f"  이미 라벨됨 → {tag} / {cls}{note}", "dim"))
    print(rule())


def show_attachments(u):
    if not u.get("attachments"):
        print(c("  첨부된 코드 없음", "dim"))
        return
    for i, a in enumerate(u["attachments"], 1):
        print(c(f"\n  ── 첨부 {i}/{len(u['attachments'])} " + "─" * 40, "mag"))
        for line in a.splitlines():
            print("  " + line)
    print()


RE_GUIDE_CMD = re.compile(r"^\?(?:([12])(?:[.\s]?(\S+))?)?$")


def ask(prompt, valid, allow_empty=False):
    """valid 안의 키 하나를 받을 때까지 반복.
    '?', '?1', '?2.6' 형태는 가이드 요청으로 그대로 돌려준다."""
    while True:
        try:
            v = input(prompt).strip().lower()
        except EOFError:
            return "q"
        except KeyboardInterrupt:
            print()
            return "q"
        if allow_empty and v == "":
            return ""
        if RE_GUIDE_CMD.match(v):
            return v
        if v in valid:
            return v
        print(c(f"  {'/'.join(valid)} 중 하나를 입력하세요. (?=가이드)", "red"))


def yn(prompt, default=None):
    while True:
        v = ask(prompt, ["y", "n"], allow_empty=default is not None)
        if v.startswith("?"):
            continue
        return default if v == "" else v == "y"


# ─────────────────────────────────────────────────────────────
# 메인 루프
# ─────────────────────────────────────────────────────────────

def collect_label(u, labeler, d):
    """한 유닛에 대한 라벨을 만든다. None이면 건너뜀/종료."""

    def handle_guide(cmd, default_which):
        m = RE_GUIDE_CMD.match(cmd)
        which, sec = m.group(1), m.group(2)
        if which is None and sec is None:
            if cmd == "?":
                show_guide(d)                 # 사용법 안내
            return
        show_guide(d, which or default_which, sec)

    while True:
        k = ask(c("  1단계 [n]ormative / [d]escriptive > ", "bold"),
                list("ndabtgpq"))
        if k.startswith("?"):
            handle_guide(k, "1"); continue
        if k == "a":
            show_attachments(u); continue
        if k in ("b", "g", "p", "q"):
            return k
        if k == "t":
            note = input("  note: ").strip()
            return ("__note__", note)
        break

    rec = {
        "sent_id": u["sent_id"],
        "labeler": labeler,
        "normative": k == "n",
        "class": None,
        "spec_strength": None,
        "public_api_only": None,
        "nondeterministic": None,
        "note": "",
        "ts": time.strftime("%Y-%m-%dT%H:%M:%S"),
    }

    if k == "d":
        return rec

    # 2단계
    while True:
        k2 = ask(c("  2단계 [e]xecutable / [s]tructural / [l]lm > ", "bold"),
                 list("esla"))
        if k2.startswith("?"):
            handle_guide(k2, "2"); continue
        if k2 == "a":
            show_attachments(u); continue
        break
    rec["class"] = k2.upper()

    while True:
        st = ask(c("  명세 강도 [s]trong / [w]eak > ", "dim"), list("sw"))
        if st.startswith("?"):
            handle_guide(st, "2"); continue
        break
    rec["spec_strength"] = "strong" if st == "s" else "weak"

    if rec["class"] == "E":
        rec["public_api_only"] = yn(
            c("  공개 API만으로 관찰 가능? [y]/n > ", "dim"), default=True)
        rec["nondeterministic"] = yn(
            c("  비결정적(타이밍·동시성·성능)? y/[n] > ", "dim"), default=False)

    note = input(c("  note (없으면 Enter) > ", "dim")).strip()
    rec["note"] = note
    return rec


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--dir", required=True, help="예: data/exp0")
    ap.add_argument("--labeler", required=True, help="A / B / C 등 본인 식별자")
    ap.add_argument("--goto", type=int, help="이 번호부터 시작 (1-based)")
    ap.add_argument("--review", action="store_true", help="붙인 라벨 훑어보기")
    args = ap.parse_args()

    d = Path(args.dir)
    units = load_units(d)
    atts = load_attachments(d)
    for u in units:
        u["attachments"] = atts.get(u["sent_id"], [])

    out = d / f"labels_{args.labeler}.jsonl"
    labels = load_labels(out)

    if args.review:
        for u in units:
            r = labels.get(u["sent_id"])
            if not r:
                continue
            tag = "N" if r["normative"] else "D"
            cls = r.get("class") or "-"
            print(f"{u['sent_id']:24} {tag}/{cls:1}  {u['text'][:70]}")
        print(f"\n{len(labels)}/{len(units)} 라벨됨")
        return

    print(rule("═"))
    print(c(f"  라벨링 — {args.labeler}", "bold"),
          f"  유닛 {len(units)}개 / 이미 라벨 {len(labels)}개")
    print(c("  ?=가이드  q=저장 후 종료  b=이전  진행 상황은 자동 저장됩니다", "dim"))
    print(c("  라벨링 중 팀원과 상의하지 마세요. 질문은 note(t)에 적으세요.", "yellow"))
    print(rule("═"))

    # 시작 위치: --goto > 첫 미라벨 유닛
    i = 0
    if args.goto:
        i = max(0, min(args.goto - 1, len(units) - 1))
    else:
        for j, u in enumerate(units):
            if u["sent_id"] not in labels:
                i = j
                break
        else:
            print(c("\n  모든 유닛이 라벨되었습니다. 수정하려면 --goto N", "green"))
            return

    while 0 <= i < len(units):
        u = units[i]
        show_unit(u, i, len(units), len(labels), labels.get(u["sent_id"]))
        res = collect_label(u, args.labeler, d)

        if res == "q":
            break
        if res == "b":
            i = max(0, i - 1)
            continue
        if res == "p":
            n = sum(1 for x in labels.values() if x["normative"])
            from collections import Counter
            cc = Counter(x["class"] for x in labels.values() if x["class"])
            print(f"\n  라벨 {len(labels)}/{len(units)}   Normative {n}   "
                  + "  ".join(f"{k} {v}" for k, v in sorted(cc.items())) + "\n")
            continue
        if res == "g":
            try:
                i = max(0, min(int(input("  이동할 번호 > ").strip()) - 1,
                               len(units) - 1))
            except ValueError:
                print(c("  숫자를 입력하세요.", "red"))
            continue
        if isinstance(res, tuple):          # note만 남기고 라벨은 나중에
            append_label(out, {"sent_id": u["sent_id"], "labeler": args.labeler,
                               "normative": None, "class": None, "note": res[1],
                               "ts": time.strftime("%Y-%m-%dT%H:%M:%S")})
            print(c("  note 저장. 라벨은 나중에 --goto 로 돌아와서 붙이세요.", "dim"))
            i += 1
            continue

        append_label(out, res)
        labels[u["sent_id"]] = res
        i += 1

    done = sum(1 for u in units if labels.get(u["sent_id"], {}).get("normative") is not None)
    print("\n" + rule("═"))
    print(f"  저장됨: {out}")
    print(f"  진행: {done}/{len(units)}")
    if done < len(units):
        print(c(f"  이어서 하려면: python3 label.py --dir {args.dir} "
                f"--labeler {args.labeler}", "dim"))
    else:
        print(c("  완료. 팀원 전원이 끝나면 집계로 넘어갑니다.", "green"))
    print(rule("═"))


if __name__ == "__main__":
    main()
