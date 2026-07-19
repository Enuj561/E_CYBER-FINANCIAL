"""
Module:  E_news_renderer
Logic:   Render news dictionary to HTML UI
Detail:  Nhận dict kết quả từ E_ai_client và vẽ ra HTML đẹp (gradient text).
"""
from datetime import datetime

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

def render_news_html(data, timeframe_text, debug_logs=None):
    """
    Nhận dict data (từ E_ai_client) và trả về HTML string.
    """
    if debug_logs is None:
        debug_logs = []
        
    if "error" in data:
        err_msg = data.get("error")
        details = data.get("details", "")
        log_html = "<br>".join(debug_logs) if debug_logs else details
        return f"""
        <div style="line-height: 1.5; font-family: Segoe UI, sans-serif;">
            <div style="font-size: 24px; font-weight: bold; margin-bottom: 15px; color: #FF5555;">
                {err_msg}
            </div>
            <div style="font-size: 16px; color: #D4D4D4; margin-bottom: 15px;">
                Dưới đây là chi tiết để debug:
            </div>
            <div style="font-size: 14px; color: #AAAAAA; background-color: #2D2D30; padding: 15px; border-radius: 5px;">
                {log_html}
            </div>
        </div>
        """

    current_date = datetime.now().strftime("%d/%m/%Y")
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
