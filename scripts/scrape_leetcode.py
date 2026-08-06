"""
爬取 LeetCode problemset 中「免費」題目的基本資料，存成 CSV。

欄位：題號、題名、網址、難度、通過率(%)、標籤(多個以 | 分隔)

資料來源：LeetCode 官方 GraphQL API (https://leetcode.com/graphql)
題目列表在網頁上是由此 API 動態載入的，並非靜態 HTML，所以直接呼叫這支 API
比爬 HTML 更穩定。免費題目以回傳欄位 isPaidOnly == False 判斷。
"""

import csv
import time
import requests

GRAPHQL_URL = "https://leetcode.com/graphql"
PROBLEM_URL_TMPL = "https://leetcode.com/problems/{slug}/"
PAGE_SIZE = 100
OUTPUT_CSV = "leetcode_free_problems.csv"

QUERY = """
query problemsetQuestionList($categorySlug: String, $limit: Int, $skip: Int, $filters: QuestionListFilterInput) {
  problemsetQuestionList: questionList(
    categorySlug: $categorySlug
    limit: $limit
    skip: $skip
    filters: $filters
  ) {
    total: totalNum
    questions: data {
      frontendQuestionId: questionFrontendId
      title
      titleSlug
      difficulty
      acRate
      paidOnly: isPaidOnly
      topicTags {
        name
      }
    }
  }
}
"""

HEADERS = {
    "Content-Type": "application/json",
    "Referer": "https://leetcode.com/problemset/",
    "User-Agent": "Mozilla/5.0",
}


def fetch_all_questions():
    questions = []
    skip = 0
    total = None

    while total is None or skip < total:
        payload = {
            "query": QUERY,
            "variables": {
                "categorySlug": "",
                "skip": skip,
                "limit": PAGE_SIZE,
                "filters": {},
            },
        }
        resp = requests.post(GRAPHQL_URL, json=payload, headers=HEADERS, timeout=15)
        resp.raise_for_status()
        data = resp.json()["data"]["problemsetQuestionList"]

        if total is None:
            total = data["total"]
            print(f"共 {total} 題，開始抓取...")

        batch = data["questions"]
        questions.extend(batch)
        skip += PAGE_SIZE
        print(f"已抓取 {min(skip, total)}/{total}")

        time.sleep(0.3)  # 稍微放慢速度，避免被限流

    return questions


def main():
    questions = fetch_all_questions()

    free_questions = [q for q in questions if not q["paidOnly"]]
    print(f"其中免費題目共 {len(free_questions)} 題")

    with open(OUTPUT_CSV, "w", newline="", encoding="utf-8-sig") as f:
        writer = csv.writer(f)
        writer.writerow(["題號", "題名", "網址", "難度", "通過率(%)", "標籤"])

        for q in sorted(free_questions, key=lambda x: int(x["frontendQuestionId"])):
            url = PROBLEM_URL_TMPL.format(slug=q["titleSlug"])
            ac_rate = round(q["acRate"], 2)
            tags = "|".join(tag["name"] for tag in q["topicTags"])
            writer.writerow(
                [
                    q["frontendQuestionId"],
                    q["title"],
                    url,
                    q["difficulty"],
                    ac_rate,
                    tags,
                ]
            )

    print(f"已寫入 {OUTPUT_CSV}")


if __name__ == "__main__":
    main()
