#!/usr/bin/env python3
"""
collect_issues.py — 라벨링 실험용 이슈 수집

동작:
  1. GraphQL로 closed 이슈 + 연결된 머지 PR 조회
  2. 조건 필터링 → 풀 크기 출력
  3. 시드 고정 무작위 추출: 실험 0용 10건 / 본 실험용 100건 (서로 겹치지 않음)
  4. 이슈별 JSON 저장
  5. 부수 집계: 이슈당 연결 PR 수, PR→이슈 연결률

사용:
  export GITHUB_TOKEN=ghp_...
  python collect_issues.py --stage pool     # 풀 크기만 확인
  python collect_issues.py --stage sample   # 추출 + 저장
  python collect_issues.py --stage prstats  # PR→이슈 연결률
"""

import argparse
import json
import os
import random
import re
import sys
import time
from datetime import datetime, timezone
from pathlib import Path

import requests

# ─────────────────────────────────────────────────────────────
# 설정 — 변경 시 반드시 보고서에 기록할 것
# ─────────────────────────────────────────────────────────────

REPOS = ["google/guava", "eclipse-vertx/vert.x"]

CREATED_AFTER = "2020-01-01"
MIN_BODY_WORDS = 20
MAX_NON_ASCII_RATIO = 0.10          # 영어 본문 판정
N_EXP0 = 10                          # 실험 0 (파라미터 결정용)
N_MAIN = 100                         # 실험 A (본 실험)
SEED_EXP0 = 20260905
SEED_MAIN = 20260905 + 1

OUT = Path("data")
API = "https://api.github.com/graphql"


# ─────────────────────────────────────────────────────────────
# GraphQL
# ─────────────────────────────────────────────────────────────

ISSUE_QUERY = """
query($owner:String!, $name:String!, $cursor:String) {
  rateLimit { remaining resetAt }
  repository(owner:$owner, name:$name) {
    issues(first:25, after:$cursor, states:CLOSED,
           orderBy:{field:CREATED_AT, direction:DESC}) {
      pageInfo { hasNextPage endCursor }
      nodes {
        number
        title
        body
        createdAt
        authorAssociation
        labels(first:20) { nodes { name } }
        comments(first:100) {
          nodes { body createdAt authorAssociation }
        }
        closedByPullRequestsReferences(first:10, includeClosedPrs:true) {
          nodes {
            number
            merged
            createdAt
            mergedAt
            files(first:100) { nodes { path } }
          }
        }
      }
    }
  }
}
"""

# PR→이슈 연결률 집계용 (라벨링과 무관, 제안서 수치)
PR_QUERY = """
query($owner:String!, $name:String!, $cursor:String) {
  repository(owner:$owner, name:$name) {
    pullRequests(first:50, after:$cursor, states:MERGED,
                 orderBy:{field:CREATED_AT, direction:DESC}) {
      pageInfo { hasNextPage endCursor }
      nodes {
        number
        createdAt
        closingIssuesReferences(first:5) { totalCount }
      }
    }
  }
}
"""


def gql(query, variables, token, retries=5):
    for attempt in range(retries):
        r = requests.post(
            API,
            json={"query": query, "variables": variables},
            headers={"Authorization": f"bearer {token}"},
            timeout=60,
        )
        if r.status_code == 200:
            payload = r.json()
            if "errors" in payload:
                msg = json.dumps(payload["errors"])[:400]
                # 스키마 불일치는 재시도해도 소용없음
                if "closedByPullRequestsReferences" in msg:
                    sys.exit(
                        "closedByPullRequestsReferences 필드 오류.\n"
                        "GitHub GraphQL 스키마가 바뀌었을 수 있습니다. "
                        "https://docs.github.com/graphql 에서 필드명을 확인하세요.\n"
                        + msg
                    )
                raise RuntimeError(msg)
            return payload["data"]
        if r.status_code in (502, 503, 504) or "rate limit" in r.text.lower():
            wait = 2 ** attempt * 5
            print(f"  재시도 {attempt+1}/{retries}, {wait}s 대기", file=sys.stderr)
            time.sleep(wait)
            continue
        raise RuntimeError(f"HTTP {r.status_code}: {r.text[:300]}")
    raise RuntimeError("재시도 초과")


# ─────────────────────────────────────────────────────────────
# 필터
# ─────────────────────────────────────────────────────────────

CREATED_AFTER_DT = datetime.fromisoformat(CREATED_AFTER).replace(tzinfo=timezone.utc)


def parse_dt(s):
    return datetime.fromisoformat(s.replace("Z", "+00:00"))


def is_english(text):
    if not text:
        return False
    non_ascii = sum(1 for c in text if ord(c) > 127)
    return non_ascii / max(len(text), 1) <= MAX_NON_ASCII_RATIO


def word_count(text):
    return len(re.findall(r"\S+", text or ""))


def merged_java_prs(issue):
    """머지되었고 .java 파일을 1개 이상 수정한 PR만."""
    out = []
    for pr in issue["closedByPullRequestsReferences"]["nodes"]:
        if not pr["merged"]:
            continue
        paths = [f["path"] for f in pr["files"]["nodes"]]
        if not any(
            p.endswith(".java") and "/test/" not in p and "/tests/" not in p
            for p in paths
        ):
            continue
        out.append(pr)
    return out


def check(issue):
    """통과하면 (True, prs), 아니면 (False, 탈락사유)."""
    if parse_dt(issue["createdAt"]) < CREATED_AFTER_DT:
        return False, "created_before_cutoff"
    body = issue["body"] or ""
    if word_count(body) < MIN_BODY_WORDS:
        return False, "body_too_short"
    if not is_english(body):
        return False, "not_english"
    prs = merged_java_prs(issue)
    if not prs:
        return False, "no_merged_java_pr"
    return True, prs


# ─────────────────────────────────────────────────────────────
# 수집
# ─────────────────────────────────────────────────────────────

def collect_repo(repo, token):
    owner, name = repo.split("/")
    cursor, seen, pool, rejected = None, 0, [], {}

    while True:
        data = gql(ISSUE_QUERY, {"owner": owner, "name": name, "cursor": cursor}, token)
        conn = data["repository"]["issues"]
        for issue in conn["nodes"]:
            seen += 1
            ok, result = check(issue)
            if not ok:
                rejected[result] = rejected.get(result, 0) + 1
                continue
            pool.append(build_record(repo, issue, result))

        print(
            f"  {repo}: 조회 {seen} / 통과 {len(pool)} "
            f"(rateLimit {data['rateLimit']['remaining']})",
            file=sys.stderr,
        )
        if not conn["pageInfo"]["hasNextPage"]:
            break
        cursor = conn["pageInfo"]["endCursor"]

    return pool, seen, rejected


def build_record(repo, issue, prs):
    """PR 생성 이전 코멘트만 남긴다 (도구가 실제로 볼 수 있는 범위)."""
    first_pr_at = min(parse_dt(p["createdAt"]) for p in prs)
    comments = [
        {
            "body": c["body"],
            "created_at": c["createdAt"],
            "author_association": c["authorAssociation"],
        }
        for c in issue["comments"]["nodes"]
        if c["body"] and parse_dt(c["createdAt"]) < first_pr_at
    ]
    return {
        "repo": repo,
        "number": issue["number"],
        "title": issue["title"],
        "body": issue["body"],
        "created_at": issue["createdAt"],
        "author_association": issue["authorAssociation"],
        "labels": [l["name"] for l in issue["labels"]["nodes"]],
        "comments": comments,
        "n_comments_before_pr": len(comments),
        "n_comments_total": len(issue["comments"]["nodes"]),
        "linked_prs": [
            {"number": p["number"], "created_at": p["createdAt"],
             "merged_at": p["mergedAt"]}
            for p in prs
        ],
        "n_linked_prs": len(prs),
        "first_pr_created_at": first_pr_at.isoformat(),
    }


# ─────────────────────────────────────────────────────────────
# 단계별 실행
# ─────────────────────────────────────────────────────────────

def stage_pool(token):
    OUT.mkdir(exist_ok=True)
    all_pool, summary = [], {}
    for repo in REPOS:
        pool, seen, rejected = collect_repo(repo, token)
        all_pool += pool
        summary[repo] = {"조회": seen, "통과": len(pool), "탈락": rejected}

    (OUT / "pool.json").write_text(
        json.dumps(all_pool, ensure_ascii=False, indent=1), encoding="utf-8"
    )

    print("\n=== 풀 집계 ===")
    for repo, s in summary.items():
        print(f"\n{repo}")
        print(f"  조회 {s['조회']} → 통과 {s['통과']}")
        for reason, n in sorted(s["탈락"].items(), key=lambda x: -x[1]):
            print(f"    - {reason}: {n}")
        rp = [i for i in all_pool if i["repo"] == repo]
        if rp:
            avg = sum(i["n_linked_prs"] for i in rp) / len(rp)
            one = sum(1 for i in rp if i["n_linked_prs"] == 1) / len(rp)
            print(f"  이슈당 연결 PR 수 평균 {avg:.2f} / 1:1 비율 {one:.1%}")

    total = len(all_pool)
    print(f"\n전체 풀 {total}건")
    need = N_EXP0 + N_MAIN
    if total < need:
        print(f"  경고: {need}건이 필요한데 {total}건뿐입니다. "
              f"CREATED_AFTER를 앞당기거나 저장소를 추가하세요.")
    else:
        # 유한모집단 보정 후 실효 표본 크기 안내
        n, N = N_MAIN, total - N_EXP0
        eff = n / (1 + (n - 1) / N)
        print(f"  본 실험 n=100의 유한모집단 보정 실효 표본: {eff:.0f}")


def stage_sample():
    pool = json.loads((OUT / "pool.json").read_text(encoding="utf-8"))
    keys = sorted(f"{i['repo']}#{i['number']}" for i in pool)
    by_key = {f"{i['repo']}#{i['number']}": i for i in pool}

    exp0_keys = random.Random(SEED_EXP0).sample(keys, N_EXP0)
    rest = sorted(set(keys) - set(exp0_keys))
    main_keys = random.Random(SEED_MAIN).sample(rest, N_MAIN)

    assert not set(exp0_keys) & set(main_keys), "표본이 겹칩니다"

    for name, ks, seed in (("exp0", exp0_keys, SEED_EXP0),
                           ("main", main_keys, SEED_MAIN)):
        d = OUT / name
        d.mkdir(parents=True, exist_ok=True)
        for k in ks:
            rec = by_key[k]
            slug = rec["repo"].split("/")[1]
            (d / f"{slug}-{rec['number']}.json").write_text(
                json.dumps(rec, ensure_ascii=False, indent=1), encoding="utf-8"
            )
        (d / "manifest.json").write_text(
            json.dumps({"seed": seed, "n": len(ks), "keys": sorted(ks),
                        "pool_size": len(pool),
                        "generated_at": datetime.now(timezone.utc).isoformat()},
                       ensure_ascii=False, indent=1),
            encoding="utf-8",
        )
        print(f"{name}: {len(ks)}건 저장 (seed={seed}) → {d}")


def stage_prstats(token, max_pages=20):
    """PR 중 연결된 이슈가 있는 비율 — 제품 적용 범위 수치."""
    print("=== PR → 이슈 연결률 ===")
    for repo in REPOS:
        owner, name = repo.split("/")
        cursor, total, linked, pages = None, 0, 0, 0
        while pages < max_pages:
            data = gql(PR_QUERY, {"owner": owner, "name": name, "cursor": cursor}, token)
            conn = data["repository"]["pullRequests"]
            for pr in conn["nodes"]:
                if parse_dt(pr["createdAt"]) < CREATED_AFTER_DT:
                    cursor = None
                    break
                total += 1
                if pr["closingIssuesReferences"]["totalCount"] > 0:
                    linked += 1
            else:
                if conn["pageInfo"]["hasNextPage"]:
                    cursor = conn["pageInfo"]["endCursor"]
                    pages += 1
                    continue
            break
        if total:
            print(f"  {repo}: {linked}/{total} = {linked/total:.1%}")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--stage", choices=["pool", "sample", "prstats"], required=True)
    args = ap.parse_args()

    token = os.environ.get("GITHUB_TOKEN")
    if not token and args.stage != "sample":
        sys.exit("GITHUB_TOKEN 환경변수를 설정하세요.")

    if args.stage == "pool":
        stage_pool(token)
    elif args.stage == "sample":
        stage_sample()
    else:
        stage_prstats(token)


if __name__ == "__main__":
    main()
