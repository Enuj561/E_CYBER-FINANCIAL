from dotenv import load_dotenv
from datetime import datetime

def summarize_news(news_list, timeframe_text, is_aggregated=False, debug_logs=None, progress_callback=None):
    """
    Gửi danh sách tin tức lên Gemini để lấy bản tóm tắt
    """
    import os
    from google import genai
    
    if not debug_logs:
        debug_logs = []
        
    if not news_list:
        log_html = "<br>".join(debug_logs)
        return f"""
        <div style="line-height: 1.5; font-family: Segoe UI, sans-serif;">
            <div style="font-size: 24px; font-weight: bold; margin-bottom: 15px; color: #FF5555;">
                Không có dữ liệu
            </div>
            <div style="font-size: 16px; color: #D4D4D4; margin-bottom: 15px;">
                Không có bản tin nào được xuất bản trong khung giờ Sếp vừa chọn. Dưới đây là chi tiết bộ lọc System Logs để debug:
            </div>
            <div style="font-size: 14px; color: #AAAAAA; background-color: #2D2D30; padding: 15px; border-radius: 5px;">
                {log_html}
            </div>
        </div>
        """

    # Vì file .env đã bị dời vào folder System, ta phải chỉ rõ đường dẫn tuyệt đối cho nó hiểu
    current_file_dir = os.path.dirname(os.path.abspath(__file__)) # .../Main Scripts/News
    project_root = os.path.dirname(os.path.dirname(current_file_dir)) # .../E_CYBER-FINANCIAL
    env_path = os.path.join(project_root, "System", ".env")
    load_dotenv(dotenv_path=env_path)
    
    api_key = os.getenv("GEMINI_API_KEY")
    
    if not api_key or api_key == "điền_api_key_của_sếp_vào_đây":
        return "LỖI: Chưa có API Key Gemini.\n\nSếp vui lòng mở file .env ở thư mục gốc (E_CYBER-FINANCIAL), tìm dòng GEMINI_API_KEY=... và dán API Key của sếp vào đó nhé!"
    
    if not news_list:
        return "Không có bản tin nào được xuất bản trong khung giờ Sếp vừa chọn."

    try:
        client = genai.Client(api_key=api_key) 
        
        # Ghép nội dung các bản tin
        content = ""
        for i, news in enumerate(news_list):
            content += f"{i+1}. Thời gian xuất bản: {news.get('published', 'Không rõ')}\nTiêu đề: {news['title']}\nTóm tắt: {news['summary']}\n\n"

        current_date = datetime.now().strftime("%d/%m/%Y")
        
        prompt_base = f"""Đóng vai một Chuyên viên Phân tích Tài chính cấp cao. Dưới đây là dữ liệu tin tức thị trường vừa được thu thập.
Nhiệm vụ của bạn là tổng hợp và viết một "Bản tin thị trường" đảm bảo 3 tiêu chí: ĐẦY ĐỦ THÔNG TIN, NGẮN GỌN và CHÍNH XÁC.
Đi thẳng vào các dữ kiện cốt lõi, loại bỏ các câu chữ hoa mỹ, lê thê."""

        if is_aggregated:
            prompt_base += "\n\nLƯU Ý ĐẶC BIỆT: Nguồn tin này được cào TỔNG HỢP từ nhiều báo khác nhau, chắc chắn sẽ CÓ NHIỀU TIN TRÙNG LẶP (cùng nói về 1 sự kiện). Bạn BẮT BUỘC phải gộp các tin trùng lặp lại thành 1 ý, tuyệt đối không liệt kê trùng lặp nội dung."

        prompt_base += """

QUAN TRỌNG: Bạn BẮT BUỘC phải trả về kết quả dưới định dạng JSON nguyên chất.
Cấu trúc JSON bắt buộc phải như sau (không kèm theo bất kỳ văn bản nào khác):
{{
  "industries": [
    {{
      "name": "Tên Ngành / Chủ đề",
      "news": [
        {{
          "time": "Ngày giờ xuất bản (bê nguyên từ input vào)",
          "content": "Nội dung tóm tắt..."
        }}
      ]
    }}
  ]
}}

Dữ liệu tin tức:
{content}"""
        
        prompt = prompt_base.format(content=content)

        import time
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
                if ("429" in error_str or "RESOURCE_EXHAUSTED" in error_str):
                    if attempt < max_retries - 1:
                        if progress_callback:
                            progress_callback(f"⚠️ API Key đang hết hạn mức (Lỗi 429).<br><br>Hệ thống đang tự động chờ {retry_delay} giây để thử lại... (Lần {attempt + 1}/{max_retries})<br>Vui lòng đợi thêm một chút nhé Sếp!")
                        time.sleep(retry_delay)
                        continue
                    else:
                        return f"""
                        <div style="line-height: 1.5; font-family: Segoe UI, sans-serif;">
                            <div style="font-size: 24px; font-weight: bold; margin-bottom: 15px; color: #FF5555;">
                                ❌ Lỗi hạn mức API Key
                            </div>
                            <div style="font-size: 16px; color: #D4D4D4;">
                                Hệ thống đã tự động thử lại 3 lần nhưng vẫn thất bại do API Key của Sếp đã hoàn toàn cạn kiệt dung lượng miễn phí (Quota).
                            </div>
                            <div style="font-size: 14px; color: #AAAAAA; margin-top: 10px;">
                                Vui lòng kiểm tra lại tài khoản Google AI Studio, thử đổi một API Key khác hoặc nâng cấp lên gói Pay-as-you-go để tiếp tục sử dụng.
                            </div>
                        </div>
                        """
                else:
                    raise e

        text_resp = response.text.strip()
        if text_resp.startswith("```json"):
            text_resp = text_resp[7:]
        elif text_resp.startswith("```"):
            text_resp = text_resp[3:]
        if text_resp.endswith("```"):
            text_resp = text_resp[:-3]
            
        import json
        data = json.loads(text_resp.strip())
        
        def gradient_text(text):
            c1 = (0, 255, 255)    # Cyan
            c2 = (192, 192, 192)  # Silver
            c3 = (255, 0, 255)    # Magenta
            
            L = len(text)
            if L == 0: return ''
            if L == 1: return f'<span style="color: rgb{c2}">{text}</span>'
            
            result = []
            for i, char in enumerate(text):
                if char.isspace():
                    result.append(char)
                    continue
                    
                ratio = i / (L - 1)
                if ratio <= 0.5:
                    local_ratio = ratio * 2
                    r = int(c1[0] + (c2[0] - c1[0]) * local_ratio)
                    g = int(c1[1] + (c2[1] - c1[1]) * local_ratio)
                    b = int(c1[2] + (c2[2] - c1[2]) * local_ratio)
                else:
                    local_ratio = (ratio - 0.5) * 2
                    r = int(c2[0] + (c3[0] - c2[0]) * local_ratio)
                    g = int(c2[1] + (c3[1] - c2[1]) * local_ratio)
                    b = int(c2[2] + (c3[2] - c2[2]) * local_ratio)
                    
                result.append(f'<span style="color: rgb({r},{g},{b})">{char}</span>')
            return ''.join(result)
            
        main_title = f"{timeframe_text} ({current_date})"
        html_output = [f'<div style="line-height: 1.5; font-family: Segoe UI, sans-serif;">']
        html_output.append(f'<div style="font-size: 24px; font-weight: bold; margin-bottom: 15px;">{gradient_text(main_title)}</div>')
        
        for idx, ind in enumerate(data.get("industries", [])):
            color = "#00FFFF" if idx % 2 == 0 else "#FF00FF"
            html_output.append(f'<div style="font-size: 16px; font-weight: bold; margin-top: 15px; margin-bottom: 5px; color: {color};">{ind.get("name", "")}</div>')
            html_output.append('<ul style="font-size: 14px; margin-top: 0px; margin-bottom: 15px; color: #D4D4D4;">')
            for n in ind.get("news", []):
                if isinstance(n, dict):
                    t = n.get("time", "")
                    c = n.get("content", "")
                    html_output.append(f'<li style="margin-bottom: 8px;"><span style="font-size: 12px; color: #888888; font-style: italic; display: inline-block; margin-bottom: 3px;">[{t}]</span><br>{c}</li>')
                else:
                    html_output.append(f'<li style="margin-bottom: 8px;">{n}</li>')
            html_output.append('</ul>')
            
        html_output.append('</div>')
        return "\n".join(html_output)
    except Exception as e:
        return f"Lỗi khi kết nối hoặc xử lý API Gemini: {str(e)}"
