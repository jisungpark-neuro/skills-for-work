---
name: nemo-todo
description: 두레이 업무 링크를 Obsidian의 "Nemo to do list" 노트의 완료·금일 작업·금주 작업·잔여 작업 섹션 중 하나에 `[제목][index]` 참조 링크로 추가한다. 두레이 링크(neurocoreaps.dooray.com)와 함께 "투두에 추가", "금일 작업에 넣어줘", "금주 작업에 추가", "잔여 작업에 넣어", "완료에 추가", "to do list에 등록", "/nemo-todo" 같은 요청이 오면 반드시 이 스킬을 쓴다.
---

# nemo-todo

두레이 링크를 받아 Obsidian `Nemo to do list` 노트의 지정 섹션에 항목을 하나 추가한다. 링크가 여러 개면 하나씩 같은 절차로 처리한다.

## 1. 노트 찾기

vault 경로는 Obsidian 설정에 있다. 노트는 vault 안의 `Neurocore/Nemo to do list.md`다.

```bash
python3 -c 'import json,os; print(*[v["path"] for v in json.load(open(os.path.expanduser("~/Library/Application Support/obsidian/obsidian.json")))["vaults"].values()], sep="\n")'
```

노트를 끝까지 읽는다. 노트는 이런 구조다.

```
[완료]
- [제목][slug]

[금일 작업]
- [제목][slug]

[금주 작업]
...
[잔여 작업]
...

[slug]: https://neurocoreaps.dooray.com/...
```

섹션 머리는 마크다운 헤딩이 아니라 `[완료]`처럼 대괄호로 감싼 한 줄이다. 참조 정의(`[slug]: url`)는 노트 맨 아래에 모여 있다.

## 2. 섹션 정하기

사용자가 말한 섹션(`완료`, `금일 작업`, `금주 작업`, `잔여 작업`)을 쓴다. "오늘" → 금일 작업, "이번 주" → 금주 작업, "나중에·백로그" → 잔여 작업, "끝났어·했어" → 완료처럼 뜻이 분명하면 그 섹션으로 정한다. 섹션을 알 수 없으면 묻지 말고 잔여 작업에 넣는다.

## 3. 제목 가져오기

링크 경로에서 마지막 19자리 숫자가 업무 ID다. 쿼리(`?...`)와 `#comment-...`는 무시한다. 링크 형태는 여러 가지다.

- `/project/tasks/{id}`, `/project/posts/{id}`
- `/task/to/{id}?...`
- `/project/{projectId}/{id}` (뒤쪽 숫자가 업무 ID)

프로젝트 ID 없이 업무를 조회할 수 있다. 토큰은 레포 루트 `.env`의 `DOORAY_API_TOKEN`을 쓰고, 토큰 값은 출력하지 않는다.

```bash
ROOT=$(git rev-parse --show-toplevel 2>/dev/null || pwd)
set -a; . "$ROOT/.env"; set +a
curl -s -H "Authorization: dooray-api $DOORAY_API_TOKEN" "https://api.dooray.com/project/v1/posts/<업무ID>" \
  | python3 -c 'import json,sys; d=json.load(sys.stdin); r=d.get("result") or {}; print(d["header"]) if not d["header"]["isSuccessful"] else print(r["subject"])'
```

- 제목은 `subject`를 그대로 쓴다. 사용자가 제목을 직접 말했으면 그 제목을 쓴다.
- 토큰이 없거나 401이 나면 `/dooray-setup`으로 먼저 설정한다.
- 조회가 실패하면(권한 없음, 삭제된 업무) 사용자에게 제목을 물어본다.

## 4. index(슬러그) 정하기

제목의 핵심을 담은 짧은 영문 kebab-case 슬러그를 만든다. 기존 노트처럼 1~3단어로 쓴다. 예: `fe-error`, `build-opt`, `logging`, `ts7`.

- 노트의 기존 참조 정의와 겹치면 다른 슬러그를 쓴다.
- 같은 URL의 참조 정의가 이미 있으면 새로 만들지 않고 그 슬러그를 재사용한다.

## 5. 노트 수정

Edit 도구로 두 곳을 고친다. 다른 줄은 건드리지 않는다.

1. **항목 추가**: 대상 섹션의 마지막 최상위 항목(하위 들여쓰기 항목 포함) 바로 다음 줄에 `- [제목][slug]`를 넣는다. 섹션이 비어 있으면 섹션 머리 바로 다음 줄에 넣는다.
2. **참조 정의 추가**: 맨 아래 참조 정의 목록의 마지막 줄 다음에 `[slug]: 링크`를 넣는다. 링크는 사용자가 준 그대로 쓴다(쿼리, `#comment-...` 포함).

같은 링크가 이미 다른 섹션의 항목으로 있으면 추가하지 말고, 어느 섹션에 있는지 알려준 뒤 옮길지 물어본다.

## 6. 보고

한 줄로 보고한다.

```
금일 작업에 추가: [NEMO 프론트엔드 API 에러 처리 표준 정비 및 Sentry 로깅 개선][fe-error]
```
