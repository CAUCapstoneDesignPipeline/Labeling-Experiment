# 요구사항 라벨링 실험

캡스톤디자인1 — LLM 생성 코드 요구사항 충족 자동 검증

실제 GitHub 이슈에 적힌 요구사항이 **어떤 방법으로 검증 가능한지** 측정한다.
실행 검증 가능한 비율이 낮으면 파이프라인 설계 자체를 바꿔야 하므로, 이 실험은
주제의 존폐를 판정하는 실험이다.

---

## 라벨러가 할 일

의존성 없음. Python 3.8 이상이면 그대로 돌아간다.

```bash
python3 label.py --dir data/exp0 --labeler A
```

`--labeler`에 본인 식별자(A / B / C)를 넣는다. **팀에서 정한 값을 그대로 쓴다.**
결과는 `data/exp0/labels_<식별자>.jsonl`에 자동 저장되며, 중간에 `q`로 끊고
같은 명령으로 다시 실행하면 이어서 진행된다.

### 진행 전에 읽을 것

| 파일 | 내용 |
|---|---|
| `LABELING_GUIDE_SENTENCE.md` | 1단계 — Normative / Descriptive |
| `LABELING_GUIDE_ESL.md` | 2단계 — E / S / L |

도구 안에서 `?`로 가이드를 바로 열 수 있지만, **시작 전에 두 가이드를 한 번은
통독한다.** 특히 경계 사례(§4 / §6)와 반드시 지킬 규칙(§5 / §7)을 본다.

`label.py`는 가이드 파일을 실행 시점에 읽는다. 판정 기준은 가이드에만 있으며,
가이드를 고치면 도구 도움말도 함께 바뀐다.

### 지켜야 할 것

- **라벨링 중 팀원과 상의하지 않는다.** 독립성이 깨지면 일치도 측정이
  무의미해지고 실험을 다시 해야 한다. 질문은 `t`를 눌러 note에 적고,
  전원이 끝난 뒤 회의에서 처리한다.
- **전원이 끝나기 전에는 서로의 `labels_*.jsonl`을 열어보지 않는다.**
- **연결된 PR의 diff를 보지 않는다.** 구현을 보면 "이게 요구사항이었구나"가
  사후적으로 생긴다.
- **이슈에 없는 기대 동작을 채워 넣지 않는다.** 당연해 보여도 문장에 없으면
  Normative가 아니다.
- 애매하면 낮은 쪽으로 내린다. (N↔D 애매 → D, E↔S 애매 → S, S↔L 애매 → L)

### 단축키

```
1단계   n Normative      d Descriptive
2단계   e Executable     s Structural     l LLM 판정만
그 외   a 첨부 코드      b 이전 유닛      t note
        g 번호 이동      p 진행 상황      ? 가이드      q 저장 후 종료
```

`?`는 가이드 파일을 그 자리에서 읽어 보여준다. 별도 창을 띄울 필요가 없고,
가이드를 고치면 도구에도 즉시 반영된다.

```
?        사용법
?1       1단계 가이드 목차        ?2       2단계 가이드 목차
?1.4     1단계 §4 경계 사례       ?2.6     2단계 §6 경계 사례
?1.5     1단계 §5 지킬 규칙       ?2.7     2단계 §7 지킬 규칙
```

1단계 프롬프트에서 `?4`를 치면 1단계 §4가, 2단계에서 `?6`을 치면 2단계 §6이
열린다. 판단이 갈리는 지점은 대부분 경계 사례 절에 적혀 있다.

`[+N code]` 표시가 있는 유닛은 `a`를 눌러 코드를 확인한다. **기대값이 코드
블록에만 있는 경우가 많아, 안 보면 E가 L로 잘못 내려간다.**

붙인 라벨을 훑어보려면:

```bash
python3 label.py --dir data/exp0 --labeler A --review
```

---

## 데이터 만드는 쪽 (담당자만)

```bash
export GITHUB_TOKEN=...          # 공개 저장소만 읽으므로 스코프 불필요
pip3 install requests

python3 collect_issues.py --stage pool      # 조건 통과 이슈 수집, 풀 크기 확인
python3 collect_issues.py --stage sample    # 시드 고정 추출 (exp0 10건 / main 100건)
python3 collect_issues.py --stage prstats   # PR→이슈 연결률 (제안서용 수치)

python3 split.py --dir data/exp0            # 유닛 분리
# → data/exp0/review.md 를 눈으로 검수한 뒤 배포
```

### units.jsonl은 한 번 배포하면 다시 만들지 않는다

`split.py`를 다시 돌리면 `sent_id` 번호가 밀려서 이미 붙인 라벨과 어긋난다.
분리 규칙을 고쳐야 하면 **라벨링 시작 전에** 고치고 전체를 재분리한다.

---

## 파일

```
collect_issues.py            이슈 수집 · 표본 추출 · PR 연결률 집계
split.py                     이슈 텍스트 → 라벨링 유닛 (결정론적, LLM 미사용)
label.py                     라벨링 CLI

LABELING_GUIDE_SENTENCE.md   1단계 가이드
LABELING_GUIDE_ESL.md        2단계 가이드
EXP0_PROTOCOL.md             사전 측정 절차 · 게이트 · 파라미터 유도

data/<set>/
  <repo>-<번호>.json          이슈 원본 (제목 · 본문 · PR 이전 코멘트)
  manifest.json               시드 · 표본 목록
  units.jsonl                 라벨링 대상 유닛          ← 공유
  attachments.json            유닛에 딸린 코드 블록      ← 공유
  review.md                   분리 결과 검수용
  split_stats.json            유닛 수 집계
  labels_<식별자>.jsonl        라벨 (라벨러별)
```

`split.py`는 실험 전용이 아니라 **파이프라인이 그대로 쓸 모듈**이다. 문장 분리를
LLM에 맡기지 않기로 했으므로, 실험과 프로덕션이 같은 코드를 쓰면 이 단계는 별도
검증이 필요 없다.

---

## 실험 구조

```
실험 0 (10건)   분리 규칙 검증 · m̄_norm · 잠정 κ
                  ↓  n_ov, E 비율 임계값 확정
실험 A (100건)  3인 라벨링 → κ₁, κ₂, E/S/L 분포
                  ↓  게이트 통과 시
실험 B          같은 유닛에 LLM 분류 → 사람 합의 라벨 대비 정확도
```

| 지표 | 게이트 |
|---|---|
| Fleiss κ₁ (Normative/Descriptive) | 95% CI 하한 > 0.61 |
| Fleiss κ₂ (E/S/L) | 95% CI 하한 > 0.61 |
| E 비율 | 95% CI 하한 > 임계값 |

κ 미달 시 조치는 표본 확대가 아니라 **가이드 개정**이다. 자세한 근거는
`EXP0_PROTOCOL.md`에 있다.

---

## 대상 저장소

`google/guava`, `eclipse-vertx/vert.x` — 둘 다 라이브러리/프레임워크다.
업무 로직 중심 애플리케이션으로의 일반화는 확인하지 못했으며, 보고서에
한계로 명시한다.
