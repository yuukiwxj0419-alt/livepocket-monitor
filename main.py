import os
import time
import requests
import threading
import http.server
import socketserver
from bs4 import BeautifulSoup

# ------------------------------------------------------------------
# 【重要】あなたのDiscord Webhook URLをここに確実に貼り付けてください
# ------------------------------------------------------------------
DISCORD_WEBHOOK_URL = "https://discord.com/api/webhooks/1510619850739810365/f1NiWVrnWCACfXmq4eJLUCAw2I_1QLV6SLerwvfc8SOqTa7CMYAFpAnrNAvFw3sWvzx0"

# 山本さん専用：関西主要トレカショップ包囲網リスト
TARGET_ORGANIZERS = [
    "2269",  # BIG MAGIC なんば店
    "1437",  # ドラゴンスター系列
    "3255",  # カードショップ竜星のPAO
    "4765",  # トレカチャンス
    "2344"   # Clove Lounge
]

# 監視キーワード（どれか1つでも入っていれば検知します）
MONITOR_KEYWORDS = ["ポケカ", "ポケモン", "ワンピース", "ONE PIECE", "ドラゴンボール", "DRAGON BALL", "抽選", "予約", "先着"]

# 重複通知を防ぐための記録部屋
NOTIFIED_URLS = set()

def send_discord(message):
    payload = {"content": message}
    try:
        requests.post(DISCORD_WEBHOOK_URL, json=payload)
    except Exception as e:
        print(f"Discord通知失敗: {e}")

# LivePocketを直接巡回するスクレイピング・エンジン
def watch_livepocket():
    print("【LivePocket強化包囲網】自動監視を開始しました。")
    send_discord("📢 【LivePocket強化包囲網】システムをアップデートしました！関西主要5ショップのゲリラ抽選・先着URLを24時間体制で同時監視します。")
    
    while True:
        try:
            for org_id in TARGET_ORGANIZERS:
                # ショップのイベント一覧ページへアクセス
                url = f"https://t.livepocket.jp/p/{org_id}"
                headers = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"}
                
                response = requests.get(url, headers=headers, timeout=15)
                if response.status_code == 200:
                    soup = BeautifulSoup(response.text, "html.parser")
                    
                    # ページ内のイベントリンクをすべて探す
                    for a_tag in soup.find_all("a", href=True):
                        href = a_tag["href"]
                        # /e/ から始まるのが個別のチケットページURL
                        if "/e/" in href:
                            full_url = href if href.startswith("http") else f"https://t.livepocket.jp{href}"
                            
                            if full_url not in NOTIFIED_URLS:
                                # タイトルの文字を取得
                                title_text = a_tag.get_text().strip()
                                
                                # キーワードに一致するかチェック
                                if any(keyword in title_text for keyword in MONITOR_KEYWORDS):
                                    message = f"@everyone 🚨【LivePocketゲリラ検知！】🚨\n山本さん、対象ショップの新着予約・抽選ページを捕捉しました！\n\n【タイトル】: {title_text}\n【購入・申込URL】: {full_url}"
                                    send_discord(message)
                                    NOTIFIED_URLS.add(full_url)
                                    
        except Exception as e:
            print(f"監視中にエラー（次回自動復旧）: {e}")
            
        # 各ショップを巡回後、3分おきに見回り（サイトに迷惑をかけない安全な速度）
        time.sleep(180)

# Renderのシャットダウン対策（生存報告用ダミーサーバー）
def run_dummy_server():
    class QuietHandler(http.server.SimpleHTTPRequestHandler):
        def log_message(self, format, *args): return
    with socketserver.TCPServer(("", 10000), QuietHandler) as httpd:
        httpd.serve_forever()

threading.Thread(target=run_dummy_server, daemon=True).start()

if __name__ == "__main__":
    watch_livepocket()
