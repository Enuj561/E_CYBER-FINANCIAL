"""
Module:  E_ai_client
Logic:   Call Gemini API to summarize financial news
Detail:  Chỉ tập trung vào việc gọi API và trả về dict JSON thuần.
"""
import os
import time
import json
from google import genai
from dotenv import load_dotenv

def summarize_news_json(news_list, is_aggregated=False, progress_callback=None):
    """
    Gửi tin tức lên Gemini API và nhận về kết quả dict thuần túy.
    """
    # Load .env
    from E_Helper.E_config import ENV_PATH
    load_dotenv(dotenv_path=ENV_PATH)
    
    api_key = os.getenv("GEMINI_API_KEY")
    if not api_key or api_key == "điền_api_key_của_sếp_vào_đây":
        return {"error": "Chưa có API Key Gemini", "details": "Vui lòng mở System/.env và cập nhật GEMINI_API_KEY."}

    if not news_list:
        return {"error": "Không có dữ liệu", "details": "Không có bản tin nào trong khung giờ."}

    # Ghép nội dung
    content = ""
    for i, news in enumerate(news_list):
        content += f"{i+1}. Thời gian xuất bản: {news.get('published', 'Không rõ')}\nTiêu đề: {news['title']}\nTóm tắt: {news['summary']}\n\n"

    prompt_base = f"""Đóng vai một Chuyên viên Phân tích Tài chính cấp cao. Dưới đây là dữ liệu tin tức thị trường vừa được thu thập.
Nhiệm vụ của bạn là tổng hợp và viết một "Bản tin thị trường" đảm bảo 3 tiêu chí: ĐẦY ĐỦ THÔNG TIN, NGẮN GỌN và CHÍNH XÁC.
Đi thẳng vào các dữ kiện cốt lõi, loại bỏ các câu chữ hoa mỹ, lê thê."""

    if is_aggregated:
        prompt_base += "\n\nLƯU Ý ĐẶC BIỆT: Nguồn tin này được cào TỔNG HỢP từ nhiều báo khác nhau, chắc chắn sẽ CÓ NHIỀU TIN TRÙNG LẶP (cùng nói về 1 sự kiện). Bạn BẮT BUỘC phải gộp các tin trùng lặp lại thành 1 ý, tuyệt đối không liệt kê trùng lặp nội dung."

    prompt_base += """

QUAN TRỌNG: Bạn BẮT BUỘC phải trả về kết quả dưới định dạng JSON nguyên chất.
Cấu trúc JSON bắt buộc phải như sau (không kèm theo bất kỳ văn bản nào khác):
{
  "industries": [
    {
      "name": "Tên Ngành / Chủ đề",
      "news": [
        {
          "time": "Ngày giờ xuất bản (bê nguyên từ input vào)",
          "content": "Nội dung tóm tắt..."
        }
      ]
    }
  ]
}

Dữ liệu tin tức:
{content}"""
    
    prompt = prompt_base.format(content=content)
    
    client = genai.Client(api_key=api_key)
    max_retries = 3
    retry_delay = 10
    response = None
    
    for attempt in range(max_retries):
        try:
            response = client.models.generate_content(
                model='gemini-2.5-flash',
                contents=prompt
            )
            break
        except Exception as e:
            error_str = str(e)
            if "429" in error_str or "RESOURCE_EXHAUSTED" in error_str:
                if attempt < max_retries - 1:
                    if progress_callback:
                        progress_callback(f"⚠️ API Key đang hết hạn mức (Lỗi 429). Đang đợi {retry_delay}s thử lại...")
                    time.sleep(retry_delay)
                    continue
                else:
                    return {"error": "Lỗi hạn mức API Key", "details": "API Key đã hoàn toàn cạn kiệt dung lượng miễn phí (Quota)."}
            else:
                return {"error": "Lỗi API Gemini", "details": str(e)}

    text_resp = response.text.strip()
    if text_resp.startswith("```json"):
        text_resp = text_resp[7:]
    elif text_resp.startswith("```"):
        text_resp = text_resp[3:]
    if text_resp.endswith("```"):
        text_resp = text_resp[:-3]
        
    try:
        data = json.loads(text_resp.strip())
        return data
    except Exception as e:
        return {"error": "Lỗi parse JSON từ Gemini", "details": str(e), "raw": text_resp}
