---
name: dooray-setup
description: Dooray API 토큰을 .env에 등록하고 인증이 되는지 확인한다. "두레이 설정", "dooray 연동", "두레이 토큰 등록", "두레이 API 연결 확인", "/dooray-setup" 요청 시 사용한다. 다른 Dooray 스킬 실행 중 DOORAY_API_TOKEN이 없거나 401(인증 실패)이 나면 이 스킬로 먼저 설정을 끝낸다.
---

# dooray-setup

Dooray API 토큰을 프로젝트 `.env`에 저장하고, 실제 호출로 인증을 확인한다. 다른 Dooray 스킬은 모두 이 `.env`의 `DOORAY_API_TOKEN`을 쓴다.

## 절차

### 1. 기존 설정 확인

`.env`는 git 레포 루트(`git rev-parse --show-toplevel`, 레포가 아니면 현재 디렉터리)에 둔다.

```bash
ROOT=$(git rev-parse --show-toplevel 2>/dev/null || pwd)
grep -q '^DOORAY_API_TOKEN=.' "$ROOT/.env" 2>/dev/null && echo "token: set" || echo "token: missing"
```

- 토큰이 있으면 3단계(연결 확인)로 간다. 확인이 성공하면 끝이다. 사용자가 교체를 원할 때만 2단계로 간다.
- 토큰이 없으면 2단계로 간다.

토큰 값은 절대 출력하지 않는다. 대화 기록과 터미널 로그에 남기 때문이다.

### 2. 토큰 등록

토큰이 없으면 사용자에게 발급 방법을 안내한다.

> Dooray 우측 상단 프로필 → **설정** → **API** → **개인 인증 토큰** → **인증 토큰 생성**

토큰을 대화창에 붙여넣지 않고 사용자가 직접 넣도록 한다. `!` 접두어를 쓰면 이 세션에서 바로 실행된다.

```
! echo 'DOORAY_API_TOKEN=발급받은토큰' >> .env
```

사용자가 대화창에 토큰을 붙여넣었다면 그 값으로 `.env`를 갱신한다. 기존 `DOORAY_API_TOKEN` 줄은 교체하고 다른 줄은 그대로 둔다.

그다음 `.env`가 커밋되지 않게 한다.

```bash
grep -qxF '.env' "$ROOT/.gitignore" 2>/dev/null || echo '.env' >> "$ROOT/.gitignore"
chmod 600 "$ROOT/.env"
```

### 3. 연결 확인

```bash
set -a; . "$ROOT/.env"; set +a
curl -s -H "Authorization: dooray-api $DOORAY_API_TOKEN" \
  https://api.dooray.com/common/v1/members/me
```

응답의 `header.isSuccessful`로 결과를 판단한다.

| 결과 | 의미 | 조치 |
|---|---|---|
| `isSuccessful: true` | 인증 성공 | `result.name`, `result.id`를 알려주고 끝 |
| HTTP 401, `resultCode: -11401001` | 토큰이 틀렸거나 만료됨 | 토큰을 새로 발급받아 2단계부터 다시 진행 |
| 연결 실패 / 타임아웃 | 네트워크 또는 도메인 문제 | 공공(`api.gov-dooray.com`) 또는 금융(`api.dooray.co.kr`) 테넌트인지 사용자에게 확인 |

## 완료 보고

성공하면 한 줄로 보고한다.

```
Dooray 연결 확인 완료: 홍길동 (memberId 1234567890123456789)
```
