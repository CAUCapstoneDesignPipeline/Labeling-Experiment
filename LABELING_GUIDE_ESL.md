# ESL Labeling Guide — 2단계 (E / S / L)

버전 2026-09-05 / 캡스톤디자인1
대상: 1단계에서 **Normative로 판정된 유닛만**

---

## 0. 이 단계가 하는 일

각 요구사항에 대해 **어떤 방법으로 검증할 수 있는가**를 판정한다.

| 라벨 | 뜻 |
|---|---|
| **E** | 코드를 실행해서 확인할 수 있다 |
| **S** | 실행하지 않고 코드 구조만 보고 확인할 수 있다 |
| **L** | 둘 다 안 되고, 의미 판단이 필요하다 |

### 주의 — E3/E2/E1/E0와 다른 것이다

파이프라인 리포트에 나오는 E3/E2/E1/E0는 **실제로 검증한 뒤** 붙는 증거 등급이다.
여기서 붙이는 E/S/L은 **검증하기 전에** 어느 방법으로 시도할지 정하는 라벨이다.

```
E/S/L        사전 — 어느 방법으로 시도할까
E3/E2/E1/E0  사후 — 실제로 무슨 증거가 나왔나
```

E로 분류해도 실행에 실패하면 E3가 못 된다. 이 가이드에서는 E3/E2/E1/E0를
신경 쓸 필요가 없다.

---

## 1. 라벨링 단위

1단계에서 `normative: true`로 판정한 유닛에만 라벨을 붙인다.
Descriptive 유닛은 `class`를 비워 둔다.

**유닛을 쪼개거나 합치지 않는다.** 한 유닛에 성격이 다른 요구가 둘 들어 있으면
더 강한 쪽(E > S > L)을 기준으로 라벨하고 `note`에 "혼합"이라고 적는다.

---

## 2. 판정 절차

**E → S → L 순서로 위에서부터 확인하고, 성립하는 가장 높은 등급을 준다.**

```
E 조건 3개를 모두 만족하는가?
   예 → E
   아니오 ↓
실행 없이 구조만으로 확인 가능한가?
   예 → S
   아니오 ↓
                → L
```

E와 S가 동시에 성립하면 **E**. 더 강한 증거를 주기 때문이다.

---

## 3. E — 실행 검증 가능

아래 셋을 **모두** 만족할 때만 E다.

### (가) 기대 결과가 명시되어 있는가

반환값, 던지는 예외, 상태 변화, 발생 이벤트 중 하나가 **이슈 텍스트에**
적혀 있어야 한다.

입력은 같은 이슈의 Descriptive 유닛(재현 절차)이나 첨부 코드 블록에서 와도
된다. 기대 결과만 이 유닛 또는 이슈 안에 있으면 된다.

### (나) 공개 API만으로 관찰 가능한가

private 필드 리플렉션이나 내부 클래스 접근이 필요하면 E가 아니다.
오라클 생성기가 구현 본문을 보지 않기 때문에, 본문을 알아야 테스트를 짤 수
있는 요구사항은 E로 다룰 수 없다.

### (다) 결정적인가

같은 입력에 항상 같은 결과가 나오는가.

**이 조건만 불만족이면** `class: "E"`, `nondeterministic: true`로 기록한다.
E에서 빼지 않는다. 집계할 때 따로 분리한다.

### 예시

| 요구사항 | 판정 |
|---|---|
| `Splitter.on(',') should preserve trailing empty fields.` | E |
| `close() should throw IllegalStateException when called twice.` | E |
| `of() should return an empty list for an empty input.` | E |
| `The map should reject null keys.` | E |
| `This class should be thread-safe.` | E, nondeterministic |
| `The handler must not block the event loop.` | E, nondeterministic |
| `Lookup should be O(1), not O(n).` | E, nondeterministic |

---

## 4. S — 구조 검증 가능

코드를 **실행하지 않고** 소스나 바이트코드의 구조만으로 판정할 수 있는 경우.

검사 대상이 되는 것:

```
접근 제한자 (public / package-private / private)
시그니처 · 오버로드 존재 여부
애노테이션 (@Deprecated, @Nullable, @Beta, @GwtCompatible …)
패키지 위치
의존 · 임포트 제약
상속 · 구현 관계
final / static 여부
javadoc 존재 여부
```

### 예시

| 요구사항 | 판정 |
|---|---|
| `This method should be package-private.` | S |
| `Foo should be deprecated in favor of Bar.` | S |
| `The new API should live in io.vertx.core.http.` | S |
| `This class should not depend on internal packages.` | S |
| `Add an overload taking a Duration.` | S |
| `The parameter should be annotated @Nullable.` | S |
| `This change must not break binary compatibility.` | S |
| `The javadoc should mention that it throws NPE.` | S |

마지막 두 개가 헷갈릴 수 있다. 이진 호환성은 시그니처 비교로, javadoc 존재는
소스 파싱으로 확인되므로 실행이 필요 없다.

---

## 5. L — 의미 판단만 가능

E도 S도 아닌 나머지. 대부분 **판정 기준이 문장 안에 없는** 경우다.

| 요구사항 | 판정 |
|---|---|
| `The error message should be clearer.` | L |
| `The API should feel more consistent with the rest of the library.` | L |
| `Consider the performance implications of this change.` | L |
| `The documentation should be easier to follow.` | L |
| `This should be more intuitive for new users.` | L |

"더 명확하게", "더 일관되게", "개선"처럼 **비교 기준이 제시되지 않은** 표현이
신호다.

---

## 6. 경계 사례

### 6.1 기대 결과가 방향만 있는 경우

```
"of() should not return null."          → E  (null이 아니면 통과, 판정 가능)
"of() should return something better."  → L  (무엇이 better인지 없음)
```

### 6.2 성능 요구

```
"Response time should stay under 50ms."   → E, nondeterministic
"Performance should be improved."         → L  (기준 없음)
```

숫자가 있으면 E, 없으면 L.

### 6.3 내부 동작에 대한 요구

```
"Should use a HashMap internally."          → S  (필드 타입 검사)
"Should not allocate on the hot path."      → L  (공개 API로 관찰 불가,
                                                  구조로도 확정 불가)
```

### 6.4 문서 요구

```
"The javadoc should mention the NPE."       → S  (존재 여부)
"The javadoc should be clearer."            → L  (기준 없음)
```

### 6.5 다른 유닛을 참조하는 경우

`same as above`, `ditto for the async variant` 같은 표현이면 참조 대상 유닛까지
읽고 판정한다.

### 6.6 여러 개가 섞인 유닛

```
"The new method should be package-private and return an empty list for null input."
        └─ S ─────────────┘              └─ E ─────────────────────┘
```

더 강한 쪽인 **E**로 라벨하고 `note`에 "혼합"이라고 적는다.

---

## 7. 반드시 지킬 규칙

**규칙 1 — 기대 결과를 채워 넣지 않는다.**

이슈에 기대 결과가 없는데 라벨러가 도메인 지식으로 "당연히 이래야지"라고
추론해서 E로 올리면 안 된다. 파일럿에서 관측된 오염(약한 명세에 없는 규칙을 LLM이
만들어낸 것)과 정확히 같은 오류이며, 이 실험의 결과를 무효화한다.

**규칙 2 — 연결된 PR의 diff를 보지 않는다.**

구현을 보면 "이건 이렇게 테스트하면 되겠네"가 사후적으로 생긴다.

**규칙 3 — E > S > L, 애매하면 내린다.**

E↔S 애매 → S. S↔L 애매 → L. 낮게 잡는 쪽이 결론을 보수적으로 만든다.

**규칙 4 — "내가 지금 짤 수 있는가"가 아니라 "원리적으로 가능한가"로 본다.**

테스트 작성 실력이나 도구 숙련도는 기준이 아니다. 단, §3의 (나) 공개 API 제약은
도구의 구조적 제약이므로 그대로 적용한다.

**규칙 5 — 라벨링 중 팀원과 상의하지 않는다.**

독립성이 깨지면 일치도 측정이 무의미해진다. 질문은 `note`에 적고 전원이 마친 뒤
회의에서 처리한다.

---

## 8. 보조 필드

| 필드 | 값 | 기준 |
|---|---|---|
| `spec_strength` | `strong` / `weak` | 기대 결과가 구체적 값·예외 타입까지 특정되면 strong, 방향만 제시하면 weak |
| `public_api_only` | bool | §3 (나) 충족 여부 |
| `nondeterministic` | bool | §3 (다) 위반 여부 |

`spec_strength` 예시:

```
"should throw IllegalStateException"      → strong
"should throw an exception"               → weak
"should not silently succeed"             → weak
```

---

## 9. 출력 스키마

1단계 라벨 파일에 필드를 추가한다.

```json
{
  "sent_id": "guava-1234-007",
  "labeler": "A",
  "normative": true,
  "class": "E",
  "spec_strength": "strong",
  "public_api_only": true,
  "nondeterministic": false,
  "note": ""
}
```

- `normative: false` → `class` 이하 전부 비움
- `class`가 `S` 또는 `L`이면 `spec_strength`만 채우고 나머지 둘은 비움
- 판단이 정말 서지 않으면 `class: null` + `note`에 사유.
  다만 규칙 3이 있으므로 드물어야 한다
