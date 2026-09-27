"""
한지영(키움증권) 텔레그램 채널(https://t.me/hedgecat0301)을 주기적으로 확인해서
새 글이 올라오면 디스코드 웹훅으로 알림을 보내고,
저녁 리포트가 참조할 수 있도록 reports/hanjiyoung/YYYY-MM-DD.md 에 글 전문을 저장하는 스크립트.

기존 hanjiyoung-alert(카카오톡 버전)와는 완전히 별개로 동작한다.
"""

import json
import os
import time
from datetime import datetime, timezone, timedelta
from pathlib import Path

import requests
from bs4 import BeautifulSoup

STATE_PATH = Path(__file__).parent / "state.json"
CHANNEL = "hedgecat0301"
CHANNEL_PREVIEW_URL = f"https://t.me/s/{CHANNEL}"

DISCORD_WEBHOOK_URL = os.environ["DISCORD_WEBHOOK_URL"]

HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
        "(KHTML, like Gecko) Chrome/124.0 Safari/537.36"
    )
}


def load_state() -> dict:
    if STATE_PATH.exists():
        return json.loads(STATE_PATH.read_text(encoding="utf-8"))
    return {"last_seen_id": 0}


def save_state(state: dict) -> None:
    STATE_PATH.write_text(json.dumps(state, ensure_ascii=False, indent=2), encoding="utf-8")


def fetch_latest_posts() -> list[dict]:
    """텔레그램 공개 채널 미리보기 페이지에서 글 목록을 가져온다.

    반환값: [{"id": int, "headline": str, "text": str, "url": str}, ...] (오래된 순으로 정렬)
    """
    resp = requests.get(CHANNEL_PREVIEW_URL, headers=HEADERS, timeout=15)
    resp.raise_for_status()
    soup = BeautifulSoup(resp.text, "html.parser")

    posts = []
    for msg in soup.select("div.tgme_widget_message"):
        data_post = msg.get("data-post")  # 예: "hedgecat0301/1234"
        if not data_post:
            continue
        try:
            post_id = int(data_post.split("/")[-1])
        except ValueError:
            continue

        text_div = msg.select_one("div.tgme_widget_message_text")
        if text_div is None:
            # 텍스트 없는 글(사진만 있는 글 등)은 건너뜀
            continue

        text = text_div.get_text(separator="\n").strip()
        if not text:
            continue

        headline = text.split("\n")[0].strip()
        if len(headline) > 80:
            headline = headline[:80] + "..."

        url = f"https://t.me/{CHANNEL}/{post_id}"
        posts.append({"id": post_id, "headline": headline, "text": text, "url": url})

    posts.sort(key=lambda p: p["id"])
    return posts


def send_discord_message(headline: str, text: str, link_url: str) -> None:
    """디스코드 웹훅으로 [제목 + 본문 미리보기 + 원문 링크] 임베드 메시지를 보낸다."""
    preview = text if len(text) <= 1500 else text[:1500] + "\n...(생략, 아래 링크에서 전문 확인)"

    payload = {
        "username": "한지영 알림봇",
        "embeds": [
            {
                "title": headline,
                "description": preview,
                "url": link_url,
                "color": 3447003,
                "footer": {"text": "키움증권 한지영 텔레그램"},
            }
        ],
    }
    for attempt in range(5):
        resp = requests.post(DISCORD_WEBHOOK_URL, json=payload, timeout=15)
        if resp.status_code == 429:
            # 디스코드 레이트리밋: 서버가 알려준 만큼 기다렸다가 재시도
            retry_after = resp.json().get("retry_after", 2)
            print(f"디스코드 레이트리밋, {retry_after}초 대기 후 재시도")
            time.sleep(float(retry_after) + 0.5)
            continue
        resp.raise_for_status()
        return
    resp.raise_for_status()


def save_daily_report_file(post: dict) -> None:
    """저녁 리포트가 읽을 수 있도록 오늘(KST) 날짜 md 파일에 글 전문을 추가한다."""
    kst = timezone(timedelta(hours=9))
    today_str = datetime.now(kst).strftime("%Y-%m-%d")
    reports_dir = Path(__file__).parent / "reports" / "hanjiyoung"
    reports_dir.mkdir(parents=True, exist_ok=True)
    file_path = reports_dir / f"{today_str}.md"

    entry = f"## {post['url']}\n\n{post['text']}\n\n"
    if file_path.exists():
        with file_path.open("a", encoding="utf-8") as f:
            f.write(entry)
    else:
        file_path.write_text(f"# {today_str} 한지영 키움증권\n\n{entry}", encoding="utf-8")


def main() -> None:
    is_first_run = not STATE_PATH.exists()
    state = load_state()
    last_seen_id = state.get("last_seen_id", 0)

    posts = fetch_latest_posts()
    if not posts:
        print("가져온 글이 없음")
        return

    if is_first_run:
        # 최초 실행: 지금까지 쌓여있던 과거 글을 한꺼번에 디스코드로 쏟아내지 않고,
        # 현재 가장 최신 글 번호를 기준점으로만 잡는다. 그 이후에 올라오는 글부터 알림이 간다.
        latest_id = posts[-1]["id"]
        state["last_seen_id"] = latest_id
        save_state(state)
        print(f"최초 실행: 기준점을 글 {latest_id}번으로 설정. 다음 새 글부터 알림/저장됩니다.")
        return

    new_posts = [p for p in posts if p["id"] > last_seen_id]

    if not new_posts:
        print("새 글 없음")
        return

    for post in new_posts:
        print(f"새 글 발견: {post['id']} - {post['headline']}")
        send_discord_message(post["headline"], post["text"], post["url"])
        save_daily_report_file(post)
        state["last_seen_id"] = post["id"]
        save_state(state)
        time.sleep(1.5)  # 디스코드 레이트리밋 예방을 위한 간격


if __name__ == "__main__":
    main()
