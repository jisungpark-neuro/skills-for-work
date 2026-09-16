#!/usr/bin/env python3
"""오전 스크럼 업무를 템플릿으로 생성하고, 직전 스크럼에 단 내 댓글을 새 업무에 복사한다.

사용: daily_scrum.py [--date YYMMDD] [--dry-run]
"""
import argparse, json, os, re, subprocess, sys, urllib.parse, urllib.request
from datetime import datetime, timedelta, timezone

BASE = "https://api.dooray.com"
PROJECT_CODE = "NEMO-APS365"
TEMPLATE_NAME = "스크럼 업무 작성 양식"
KST = timezone(timedelta(hours=9))


def load_token():
    root = subprocess.run(["git", "rev-parse", "--show-toplevel"], capture_output=True, text=True).stdout.strip() or os.getcwd()
    try:
        for line in open(os.path.join(root, ".env")):
            if line.startswith("DOORAY_API_TOKEN="):
                return line.split("=", 1)[1].strip().strip("'\"")
    except FileNotFoundError:
        pass
    sys.exit("DOORAY_API_TOKEN이 없습니다. /dooray-setup 으로 먼저 설정하세요.")


def api(method, path, token, body=None, **query):
    url = BASE + path + ("?" + urllib.parse.urlencode(query) if query else "")
    req = urllib.request.Request(url, method=method, headers={"Authorization": f"dooray-api {token}", "Content-Type": "application/json"},
                                 data=json.dumps(body).encode() if body is not None else None)
    try:
        with urllib.request.urlopen(req) as r:
            res = json.load(r)
    except urllib.error.HTTPError as e:
        sys.exit(f"{method} {path} -> HTTP {e.code}: {e.read().decode()[:300]}")
    if not res["header"]["isSuccessful"]:
        sys.exit(f"{method} {path} -> {res['header']}")
    return res["result"]


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--date", help="YYMMDD (기본: 오늘 KST)")
    ap.add_argument("--dry-run", action="store_true", help="생성/댓글 작성 없이 계획만 출력")
    a = ap.parse_args()
    today = a.date or datetime.now(KST).strftime("%y%m%d")
    if not re.fullmatch(r"\d{6}", today):
        sys.exit("--date는 YYMMDD 6자리여야 합니다.")
    tok = load_token()

    me = api("GET", "/common/v1/members/me", tok)["id"]
    projects = [p for p in api("GET", "/project/v1/projects", tok, member="me", page=0, size=100) if p["code"] == PROJECT_CODE]
    if not projects:
        sys.exit(f"프로젝트 {PROJECT_CODE}를 찾을 수 없습니다.")
    pid = projects[0]["id"]
    tmpls = [t for t in api("GET", f"/project/v1/projects/{pid}/templates", tok, page=0, size=100) if t["templateName"] == TEMPLATE_NAME]
    if not tmpls:
        sys.exit(f"템플릿 '{TEMPLATE_NAME}'을 찾을 수 없습니다.")
    tmpl = api("GET", f"/project/v1/projects/{pid}/templates/{tmpls[0]['id']}", tok)
    suffix = tmpl["subject"]  # "오전 스크럼"
    subject = f"{today} {suffix}"

    # 기존 스크럼 목록: 제목 날짜 기준으로 오늘 것과 직전 것을 찾는다 (생성일은 전날일 수 있음).
    # subjects= 검색은 색인 지연으로 방금 만든 업무가 안 잡혀 중복 생성이 났었다. 필터 없는 최신순 목록을 훑는다.
    dated = {}
    for page in range(10):
        posts = api("GET", f"/project/v1/projects/{pid}/posts", tok, page=page, size=100, order="-createdAt")
        for p in posts:
            m = re.fullmatch(rf"(\d{{6}}) {re.escape(suffix)}", p["subject"].strip())
            if m:
                dated.setdefault(m.group(1), p)
        if not posts or any(d < today for d in dated):
            break
    existing = dated.get(today)
    prev_dates = sorted(d for d in dated if d < today)
    prev = dated[prev_dates[-1]] if prev_dates else None

    # 직전 스크럼에서 내 댓글(가장 최근 것) 찾기
    my_comment = None
    if prev:
        logs = api("GET", f"/project/v1/projects/{pid}/posts/{prev['id']}/logs", tok, page=0, size=100, order="createdAt")
        mine = [l for l in logs if l["type"] == "comment" and l["creator"]["member"]["organizationMemberId"] == me]
        my_comment = mine[-1] if mine else None

    link = lambda p: f"https://neurocoreaps.dooray.com/project/{pid}/{p['id']}"
    print(f"새 스크럼: {subject}" + (f"  (이미 존재: {link(existing)})" if existing else ""))
    print(f"직전 스크럼: {prev['subject'] if prev else '없음'}" + (f"  내 댓글 {'있음' if my_comment else '없음'}" if prev else ""))
    if a.dry_run:
        if my_comment:
            print("\n--- 복사할 댓글 ---\n" + my_comment["body"]["content"])
        return

    if existing:
        post = existing
    else:
        member = lambda u: {"type": "member", "member": {"organizationMemberId": u["member"]["organizationMemberId"]}}
        post = api("POST", f"/project/v1/projects/{pid}/posts", tok, {
            "subject": subject,
            "body": tmpl["body"],
            "users": {"to": [member(u) for u in tmpl["users"]["to"]], "cc": [member(u) for u in tmpl["users"]["cc"]]},
            "tagIds": [t["id"] for t in tmpl.get("tags", [])],
            "priority": tmpl.get("priority", "none"),
            "dueDateFlag": tmpl.get("dueDateFlag", False),
        })
        print(f"생성 완료: {link(post)}")

    if my_comment:
        # 이미 같은 댓글을 붙여넣었으면 중복 방지
        logs = api("GET", f"/project/v1/projects/{pid}/posts/{post['id']}/logs", tok, page=0, size=100, order="createdAt")
        if any(l["type"] == "comment" and l["creator"]["member"]["organizationMemberId"] == me for l in logs):
            print("댓글: 새 스크럼에 이미 내 댓글이 있어 건너뜀")
        else:
            api("POST", f"/project/v1/projects/{pid}/posts/{post['id']}/logs", tok, {"body": my_comment["body"]})
            print(f"댓글 복사 완료 ({prev['subject']} → {subject})")
    else:
        print("댓글: 복사할 직전 댓글이 없어 건너뜀")
    print(f"\n{link(post)}")


if __name__ == "__main__":
    main()
