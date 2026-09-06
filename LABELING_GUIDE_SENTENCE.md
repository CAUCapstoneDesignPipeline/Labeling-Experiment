# Context Labeling Guide — 1단계 (Normative / Descriptive)

버전 2026-09-05 / 캡스톤디자인1
대상: `google/guava`, `eclipse-vertx/vert.x` 이슈 텍스트

---

## 0. 이 단계가 하는 일

이슈 텍스트의 유닛 하나하나에 대해 **그것이 요구사항인지** 판정한다.
Normative로 판정된 유닛만 2단계(E/S/L)로 넘어간다.

용어를 층위별로 구분한다. 섞으면 판단이 흐려진다.

| 층위 | 구분 | 이 가이드의 범위 |
|---|---|---|
| 소스 | Normative Source / Implementation Source | 밖 |
| **유닛** | **Normative / Descriptive** | **여기** |

이 실험에서 다루는 텍스트는 이슈 본문과 코멘트뿐이므로 **소스는 이미 전부
Normative Source다.** 그 안에서 요구사항 유닛과 나머지를 가르는 것이 1단계다.
PR 설명·커밋 메시지·diff는 애초에 수집 대상이 아니다.

---

## 1. 라벨링 단위

분리 스크립트가 만든 유닛 파일을 그대로 쓴다. **유닛을 임의로 쪼개거나 합치지
않는다.** 라벨러마다 유닛이 달라지면 일치도 계산이 불가능하다.

쪼개야 한다고 판단되면 라벨은 그대로 붙이고 `note`에 사유를 적는다.
분리 규칙 개정은 회의에서 처리하고, 개정 시 전체를 재분리한다.

포함 범위:

- 이슈 제목 (`block_type=title`)
- 이슈 본문
- 연결된 PR이 열리기 **이전에** 작성된 코멘트

본문 안의 마크다운 헤딩(`### Steps to reproduce` 등)은 템플릿 구조이므로 유닛이
아니다. 이슈 제목은 다르다 — 요구사항이 제목에만 압축되어 있는 경우가 많으므로
유닛으로 포함한다.

---

## 2. 판정 절차

### 핵심 질문

> **PR이 머지된 뒤 이 문장을 코드에 대고 "지켜졌는가"라고 물을 수 있는가?**

물을 수 있으면 Normative, 없으면 Descriptive.

바꿔 말하면 Normative는 **완성된 코드가 만족해야 할 조건**이고, Descriptive는
그 외 전부 — 현재 상태, 과거 사실, 환경, 재현 절차, 배경, 대화 — 다.

### 3단계로 확인

**Q1. 주어가 시스템·코드·API인가?**

사람, 일정, 프로젝트 운영이 주어면 Descriptive.

```
"The client should reconnect."           → 시스템   → Q2로
"I'll submit a PR tomorrow."             → 사람     → Descriptive
"This should be fixed before the 33.0 release."  → 일정 → Descriptive
```

**Q2. 당위인가 서술인가?**

```
당위    should / must / needs to / has to / is expected to
        shouldn't / must not / never
        명령형 (Make X return Y)
        제안형 (It would be nice if / Consider adding)

서술    현재형·과거형 사실 진술
        currently / at the moment / as of
```

**Q3. 이 유닛을 지우면 요구사항이 하나 사라지는가?**

사라지면 Normative. 배경 설명만 얇아지면 Descriptive.

---

## 3. 판단 신호

### Normative 쪽

| 유형 | 예시 |
|---|---|
| 기대 동작 | `Calling of() with a null element should throw NPE.` |
| 금지 | `The handler must not block the event loop.` |
| 조건부 | `If the buffer is full, write() should return false.` |
| 계약 인용 | `The javadoc states that it returns an empty list.` |
| 구조 제약 | `The new API should live in io.vertx.core.http.` |
| 확정된 제안 | `Add an overload taking a Duration.` |
| 약한 요구 | `It would be nice if the builder rejected duplicates.` |

계약 인용이 Normative인 이유: javadoc·스펙은 코드가 만족해야 할 계약을 진술하며,
"코드에 대고 지켜졌는가"를 물을 수 있다.

### Descriptive 쪽

| 유형 | 예시 |
|---|---|
| 현상 서술 | `of() with a null element throws NPE.` |
| 재현 절차 | `Run the snippet below with an empty input.` |
| 환경 | `JDK 21, macOS 14, Guava 33.0.` |
| 이력 | `This has been broken since 32.0.` |
| 배경·동기 | `We rely on this in a high-throughput service.` |
| 타 시스템 | `Apache Commons handles this differently.` |
| 메타 대화 | `Thanks for the report.` / `Assigning to @x.` |
| 미확정 질문 | `Should this throw or return empty?` |

---

## 4. 경계 사례

### 4.1 현상 서술과 기대 동작이 붙어 있는 형태 — 가장 흔함

버그 리포트의 표준 형태다. **기대 동작 쪽만** Normative로 잡는다.

```
"of() returns null for an empty input, but it should return an empty list."
      └─ Descriptive ─────────┘  └──── Normative ────────────────┘
```

같은 유닛 안에 둘 다 들어 있으면 **요구를 담은 쪽을 기준으로 Normative**로 잡고
`note`에 "혼합"이라고 적는다. 유닛을 쪼개지 않는다.

### 4.2 기대 동작이 없는 현상 서술 — 반드시 Descriptive

```
"of() returns null for an empty input."          → Descriptive
```

"당연히 빈 리스트여야지"라고 생각되더라도 **문장에 없으면 Normative가 아니다.**
이 판단이 이 가이드에서 가장 중요하다(§5 규칙 1).

이런 이슈가 많이 나오는 것은 정상이다. 실제로 버그 리포트의 상당수가 기대 동작을
명시하지 않으며, 그 비율을 재는 것이 이 실험의 목적 중 하나다.

### 4.3 재현 절차

Descriptive지만 **버리는 정보가 아니다.**

```
"Run: Splitter.on(',').split(\"a,,b\")"    → Descriptive (입력을 제공)
"It should yield three elements."          → Normative  (기대값을 제공)
```

2단계에서 E 판정을 할 때는 같은 이슈의 Descriptive 유닛과 첨부 코드를 **근거로
참조할 수 있다.** 라벨은 Normative 유닛에 붙지만, 그 유닛이 E인지 판단할 때
입력이 어디서 왔는지는 상관없다.

### 4.4 구현 방법에 대한 언급

최종 산출물을 제약하면 Normative, 방법론 잡담이면 Descriptive.

```
"Add an overload taking a Duration."              → Normative (API가 제약됨)
"We could refactor this whole class someday."     → Descriptive
"Maybe caching would help, not sure."             → Descriptive
```

기준은 **확신의 강도가 아니라 제약의 유무**다. "It would be nice if the builder
rejected duplicates"는 약하지만 산출물을 제약하므로 Normative다.

### 4.5 질문과 그 답

```
"Should this throw or return empty?"     → Descriptive (미확정)
"It should throw."                       → Normative  (확정)
```

### 4.6 철회·번복

뒤 코멘트가 앞 요구를 뒤집는 경우, **둘 다 원래대로 라벨하고** `note`에
`superseded by <sent_id>` 또는 `supersedes <sent_id>`를 적는다.
1단계에서 처리하지 않는다.

### 4.7 반복

같은 요구가 본문과 코멘트에 각각 있으면 **둘 다 Normative**로 잡고 `note`에
중복 표시. 중복 제거는 집계 단계의 일이다.

---

## 5. 반드시 지킬 규칙

**규칙 1 — 없는 요구를 채워 넣지 않는다.**

문장에 기대 동작이 없는데 라벨러가 도메인 지식으로 추론해 Normative로 올리면
안 된다. 파일럿에서 관측된 오염(약한 명세에 없는 규칙을 LLM이 만들어낸 것)과
같은 오류이며, 이 실험의 측정값을 무효화한다.

**규칙 2 — 연결된 PR의 diff를 보지 않는다.**

구현을 보면 "아, 이게 요구사항이었구나"가 사후적으로 생긴다. 유닛 파일에도 diff를
포함시키지 않는다.

**규칙 3 — 애매하면 Descriptive.**

낮게 잡는 쪽이 결론을 보수적으로 만든다. 놓친 요구사항은 E0로 드러나지만,
없는 요구사항을 만들면 근거 없는 판정이 생긴다.

**규칙 4 — 작성자 지위로 판정하지 않는다.**

메인테이너가 썼는지 외부 사용자가 썼는지는 라벨에 반영하지 않는다.
작성자 정보(`author_association`)는 API에서 자동으로 채워 넣고 분석 축으로만 쓴다.

**규칙 5 — 라벨링 중 팀원과 상의하지 않는다.**

독립성이 깨지면 kappa가 부풀어 측정 자체가 무의미해진다.
질문은 `note`에 적고 전원이 라벨링을 마친 뒤 회의에서 처리한다.

---

## 6. 출력 스키마

유닛 파일(공통)에 라벨만 추가해 라벨러별 별도 파일로 저장한다.

```json
{
  "sent_id": "guava-1234-007",
  "labeler": "A",
  "normative": true,
  "note": ""
}
```

`note` 사용 예: `혼합`, `중복`, `superseded by guava-1234-019`,
`쪼개야 할 것 같음`, `판단 불가`

판단이 정말 서지 않으면 `normative: null` + `note`에 사유. 집계에서 제외하고
회의에서 처리한다. 다만 §5 규칙 3이 있으므로 이 경우는 드물어야 한다.

---

## 7. 집계 시 보고할 값

```
전체 유닛 수 M_all
라벨러별 Normative 수 N_A / N_B / N_C
교집합 Normative 수 N_∩          ← m̄_norm 계산은 이 값으로
개인 평균과 교집합의 격차

단순 일치율 P_o
주변분포 (Normative : Descriptive 비율)
Fleiss κ₁ + 부트스트랩 95% CI
pairwise Cohen (AB / AC / BC)
```

### kappa 역설 주의

Descriptive가 70%를 넘는 쏠린 분포가 예상된다. 이 경우 단순 일치율이 85%여도
kappa가 0.4대로 내려갈 수 있다. 우연 일치 기대값이 커지기 때문이며, 가이드가
나쁜 것이 아니라 지표의 성질이다.

**일치율·kappa·주변분포를 항상 함께 보고**해야 원인을 구분할 수 있다.

```
κ 낮음 + 분포 고름  → 가이드가 애매함  → 가이드 개정
κ 낮음 + 분포 쏠림  → 지표의 성질      → 일치율 병기로 설명
```

### κ₁이 낮으면 κ₂까지 무너진다

2단계 대상은 **3인 전원이 Normative로 본 유닛(교집합)** 이다.
κ₁이 낮으면 교집합이 작아져 κ₂의 표본이 부족해진다.
1단계 게이트를 통과하지 못하면 2단계 결과는 해석하지 않는다.

---

## 8. 게이트

| 지표 | 기준 |
|---|---|
| Fleiss κ₁ | 95% CI 하한 > 0.61 |

미달 시 조치는 표본 확대가 아니라 **가이드 개정**이다.
불일치 사례를 모아 §3·§4를 구체화하고 10건을 재라벨링한다.
