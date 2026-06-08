from datetime import datetime, timedelta
import feedparser
from bs4 import BeautifulSoup

RSS_FEEDS = {
    "Tạp chí kinh tế VN": {
        "Vĩ mô & Tiền tệ": [
            "https://vneconomy.vn/tai-chinh.rss",
            "https://vneconomy.vn/kinh-te-the-gioi.rss"
        ],
        "Thị trường & Đầu tư": [
            "https://vneconomy.vn/chung-khoan.rss",
            "https://vneconomy.vn/dia-oc.rss",
            "https://vneconomy.vn/nhip-cau-doanh-nghiep.rss"
        ],
        "Công nghệ": [
            "https://vneconomy.vn/kinh-te-so.rss",
            "https://vneconomy.vn/cong-nghe-startup.rss"
        ]
    },
    "Báo Đầu tư": {
        "Vĩ mô & Tiền tệ": [
            "https://baodautu.vn/dau-tu-tai-chinh.rss",
            "https://baodautu.vn/quoc-te.rss"
        ],
        "Thị trường & Đầu tư": [
            "https://baodautu.vn/thi-truong-dia-oc.rss",
            "https://baodautu.vn/toan-canh-dau-tu.rss",
            "https://baodautu.vn/thong-tin-doanh-nghiep.rss"
        ],
        "Công nghệ": [
            "https://baodautu.vn/khoa-hoc-va-cong-nghe.rss",
            "https://baodautu.vn/kinh-te-so.rss"
        ]
    },
    "Tạp chí ĐT Kinh doanh": {
        "Vĩ mô & Tiền tệ": [
            "https://vnbusiness.vn/rss/tai-chinh.rss"
        ],
        "Thị trường & Đầu tư": [
            "https://vnbusiness.vn/rss/doanh-nghiep.rss",
            "https://vnbusiness.vn/rss/bat-dong-san.rss",
            "https://vnbusiness.vn/rss/chung-khoan.rss"
        ],
        "Công nghệ": [
            "https://vnbusiness.vn/rss/cong-nghe.rss",
            "https://vnbusiness.vn/rss/startup.rss"
        ]
    },
    "Vietnamnet": {
        "Vĩ mô & Tiền tệ": [
            "https://vietnamnet.vn/rss/the-gioi.rss",
            "https://vietnamnet.vn/rss/tai-chinh.rss"
        ],
        "Thị trường & Đầu tư": [
            "https://vietnamnet.vn/bat-dong-san.rss",
            "https://vietnamnet.vn/chung-khoan.rss",
            "https://vietnamnet.vn/doanh-nghiep.rss"
        ],
        "Công nghệ": [
            "https://vietnamnet.vn/cong-nghe.rss",
            "https://vietnamnet.vn/kinh-te-so.rss"
        ]
    }
}

def fetch_news(source, category, timeframe="24h"):
    news_items = []
    debug_logs = []
    now = datetime.now()
    
    # Logic xác định khung giờ thông minh
    if now.hour < 12:
        start_morning = now.replace(hour=0, minute=0, second=0, microsecond=0)
        end_morning = now.replace(hour=11, minute=59, second=59)
        yesterday = now - timedelta(days=1)
        start_afternoon = yesterday.replace(hour=12, minute=0, second=0, microsecond=0)
        end_afternoon = yesterday.replace(hour=23, minute=59, second=59)
    else:
        start_morning = now.replace(hour=0, minute=0, second=0, microsecond=0)
        end_morning = now.replace(hour=11, minute=59, second=59)
        start_afternoon = now.replace(hour=12, minute=0, second=0, microsecond=0)
        end_afternoon = now.replace(hour=23, minute=59, second=59)
        
    urls_to_fetch = []
    if source == "Tổng hợp":
        for src in RSS_FEEDS:
            if category in RSS_FEEDS[src]:
                urls_to_fetch.extend(RSS_FEEDS[src][category])
    else:
        if source in RSS_FEEDS and category in RSS_FEEDS[source]:
            urls_to_fetch.extend(RSS_FEEDS[source][category])
            
    for url in urls_to_fetch:
        try:
            feed = feedparser.parse(url)
            if not feed.entries:
                debug_logs.append(f"❌ [{url}] Lỗi: Link hỏng hoặc feed trống.")
                continue
                
            fetched_count = 0
            skipped_count = 0
            newest_skipped = None
            
            for entry in feed.entries:
                try:
                    pub_tuple = entry.published_parsed
                    if not pub_tuple:
                        continue
                    
                    pub_dt = datetime(*pub_tuple[:6])
                    pub_dt = pub_dt + timedelta(hours=7)
                    
                    valid = False
                    if timeframe == "24h":
                        if now - pub_dt <= timedelta(hours=24):
                            valid = True
                    elif timeframe == "morning":
                        if start_morning <= pub_dt <= end_morning:
                            valid = True
                    elif timeframe == "afternoon":
                        if start_afternoon <= pub_dt <= end_afternoon:
                            valid = True
                            
                    if valid:
                        fetched_count += 1
                        sapo = entry.summary if hasattr(entry, 'summary') else ""
                        sapo_text = BeautifulSoup(sapo, "html.parser").get_text().strip()
                        
                        news_items.append({
                            "title": entry.title,
                            "summary": sapo_text,
                            "link": entry.link,
                            "published": pub_dt.strftime("%Y-%m-%d %H:%M:%S")
                        })
                    else:
                        skipped_count += 1
                        if newest_skipped is None or pub_dt > newest_skipped:
                            newest_skipped = pub_dt
                except Exception:
                    continue
            
            if fetched_count > 0:
                debug_logs.append(f"✅ [{url}] Lấy thành công {fetched_count} bài.")
            else:
                if skipped_count > 0 and newest_skipped:
                    delta_hours = int((now - newest_skipped).total_seconds() / 3600)
                    debug_logs.append(f"⚠️ [{url}] Bỏ qua {skipped_count} bài. Sai lệch giờ (bài mới nhất cách đây khoảng {delta_hours} tiếng).")
                else:
                    debug_logs.append(f"⚠️ [{url}] Không có bài viết nào hợp lệ.")
                    
        except Exception as e:
            debug_logs.append(f"❌ [{url}] Lỗi parse dữ liệu: {str(e)}")
                
    return news_items, debug_logs
