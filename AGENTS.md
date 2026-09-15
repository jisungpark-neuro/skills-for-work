# skills-for-work

Dooray API를 연동해 업무에 활용하는 에이전트 스킬 모음 레포.

## 개요

- 각 스킬은 Dooray API(프로젝트/업무, 메신저, 캘린더, 위키, 드라이브 등)를 호출해 반복 업무를 자동화한다.
- 스킬 하나당 디렉터리 하나: `skills/<skill-name>/SKILL.md` (필요 시 스크립트 동봉).

## Dooray API

- Base URL: `https://api.dooray.com` (민간 클라우드 기준)
- 인증 헤더: `Authorization: dooray-api {API_TOKEN}`
- 토큰은 환경변수(`DOORAY_API_TOKEN`)로 주입한다. 레포에 커밋 금지.
