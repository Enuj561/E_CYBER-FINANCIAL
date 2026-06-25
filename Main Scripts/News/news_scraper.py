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

def fetch_news(source, category, target_date=None):
    """
    Cào tin tức từ RSS feeds.
    
    Args:
        source: Tên nguồn báo hoặc "Tổng hợp"
        category: Lĩnh vực tin tức
        target_date: (Optional) datetime.date - Ngày cần lấy tin.
                     Nếu None → dùng logic realtime (datetime.now()).
                     Nếu truyền vào → lấy tin trong khung giờ của ngày đó.
    """
    news_items = []
    debug_logs = []
    now = datetime.now()
    
    # Logic khung giờ: 18:00 hôm trước → 18:00 hôm nay
    # Chu kỳ "ngày tài chính" neo tại 18:00
    if target_date is not None:
        # Backfill / Batch mode: lấy trọn chu kỳ "ngày tài chính"
        # Chu kỳ = hôm trước 18:00 → ngày target 18:00 (24 tiếng)
        target_dt = datetime.combine(target_date, datetime.min.time())
        target_18 = target_dt.replace(hour=18, minute=0, second=0, microsecond=0)
        start_time = target_18 - timedelta(days=1)  # Hôm trước 18:00
        end_time = target_18                         # Ngày target 18:00
    else:
        # Realtime mode: logic hiện tại (dùng datetime.now())
        today_18 = now.replace(hour=18, minute=0, second=0, microsecond=0)
        
        if now.hour >= 18:
            # Đã qua 18:00 → chu kỳ mới: hôm nay 18:00 → hiện tại
            start_time = today_18
            end_time = now
        else:
            # Chưa đến 18:00 → chu kỳ cũ: hôm qua 18:00 → hôm nay 18:00
            start_time = today_18 - timedelta(days=1)
            end_time = today_18
        
    debug_logs.append(f"📅 Khung giờ lấy tin: {start_time.strftime('%d/%m %H:%M')} → {end_time.strftime('%d/%m %H:%M')}")
        
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
                    
                    valid = start_time <= pub_dt <= end_time
                            
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
