"""
微信聊天记录数据导出器
=======================
功能: 将聊天记录导出为 TXT / CSV / HTML 格式。
HTML 格式模拟微信气泡对话 UI，方便截图分享。

所有数据处理完全在本地完成，无任何网络请求。
"""

import os
import csv
import html as html_lib


def export_all(messages: list, output_dir: str,
               my_name: str, friend_name: str) -> dict:
    """导出所有格式，返回文件路径字典。"""
    os.makedirs(output_dir, exist_ok=True)
    results = {}
    
    # 筛选文本消息用于导出
    text_msgs = [m for m in messages if m["msg_type"] == "text"]
    
    try:
        path = export_txt(text_msgs, output_dir, my_name, friend_name)
        results["txt"] = path
    except Exception as e:
        results["txt_error"] = str(e)
    
    try:
        path = export_csv(text_msgs, output_dir, my_name, friend_name)
        results["csv"] = path
    except Exception as e:
        results["csv_error"] = str(e)
    
    try:
        path = export_html(text_msgs, output_dir, my_name, friend_name)
        results["html"] = path
    except Exception as e:
        results["html_error"] = str(e)
    
    return results


def export_txt(messages: list, output_dir: str,
               my_name: str, friend_name: str) -> str:
    """导出为纯文本格式。"""
    path = os.path.join(output_dir, "chat_export.txt")
    
    with open(path, "w", encoding="utf-8") as f:
        f.write(f"=== {my_name} 与 {friend_name} 的聊天记录 ===\n")
        f.write(f"共 {len(messages)} 条文本消息\n")
        f.write("=" * 50 + "\n\n")
        
        current_date = ""
        for m in messages:
            msg_date = m["time"][:10]
            if msg_date != current_date:
                current_date = msg_date
                f.write(f"\n--- {current_date} ---\n\n")
            
            time_part = m["time"][11:]  # HH:MM:SS
            f.write(f"[{time_part}] {m['sender']}: {m['content']}\n")
    
    return path


def export_csv(messages: list, output_dir: str,
               my_name: str, friend_name: str) -> str:
    """导出为 CSV 格式。"""
    path = os.path.join(output_dir, "chat_export.csv")
    
    with open(path, "w", encoding="utf-8-sig", newline="") as f:
        writer = csv.writer(f)
        writer.writerow(["时间", "发送者", "内容", "是否自己发送"])
        for m in messages:
            writer.writerow([m["time"], m["sender"], m["content"], "是" if m["is_me"] else "否"])
    
    return path


def export_html(messages: list, output_dir: str,
                my_name: str, friend_name: str) -> str:
    """导出为微信气泡对话 UI 风格的 HTML。"""
    path = os.path.join(output_dir, "chat_export.html")
    
    # 生成消息气泡 HTML
    bubbles = []
    current_date = ""
    
    for m in messages:
        msg_date = m["time"][:10]
        if msg_date != current_date:
            current_date = msg_date
            bubbles.append(f'<div class="date-divider"><span>{current_date}</span></div>')
        
        time_part = m["time"][11:16]  # HH:MM
        content = html_lib.escape(m["content"])
        # 处理换行
        content = content.replace("\n", "<br>")
        
        if m["is_me"]:
            bubbles.append(f'''
            <div class="msg-row me">
                <div class="msg-bubble me">
                    <div class="msg-content">{content}</div>
                    <div class="msg-time">{time_part}</div>
                </div>
                <div class="avatar me">{html_lib.escape(my_name[:1])}</div>
            </div>''')
        else:
            bubbles.append(f'''
            <div class="msg-row friend">
                <div class="avatar friend">{html_lib.escape(friend_name[:1])}</div>
                <div class="msg-bubble friend">
                    <div class="msg-content">{content}</div>
                    <div class="msg-time">{time_part}</div>
                </div>
            </div>''')
    
    html_content = f'''<!DOCTYPE html>
<html lang="zh-CN">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>{my_name} 与 {friend_name} 的聊天记录</title>
<style>
* {{ margin: 0; padding: 0; box-sizing: border-box; }}

body {{
    font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", "PingFang SC",
                 "Hiragino Sans GB", "Microsoft YaHei", sans-serif;
    background: #EDEDED;
    color: #333;
    padding: 0;
}}

.chat-header {{
    background: #2C3E50;
    color: #fff;
    padding: 18px 20px;
    text-align: center;
    font-size: 17px;
    font-weight: 600;
    letter-spacing: 0.5px;
    position: sticky;
    top: 0;
    z-index: 100;
    box-shadow: 0 2px 8px rgba(0,0,0,0.15);
}}

.chat-header .subtitle {{
    font-size: 12px;
    opacity: 0.7;
    margin-top: 4px;
    font-weight: 400;
}}

.chat-container {{
    max-width: 480px;
    margin: 0 auto;
    padding: 12px 10px 40px;
}}

.date-divider {{
    text-align: center;
    margin: 18px 0 12px;
}}

.date-divider span {{
    background: #CECECE;
    color: #fff;
    font-size: 12px;
    padding: 3px 10px;
    border-radius: 4px;
}}

.msg-row {{
    display: flex;
    align-items: flex-start;
    margin: 6px 0;
    gap: 8px;
}}

.msg-row.me {{
    flex-direction: row-reverse;
}}

.avatar {{
    width: 40px;
    height: 40px;
    border-radius: 6px;
    display: flex;
    align-items: center;
    justify-content: center;
    font-size: 16px;
    font-weight: 600;
    color: #fff;
    flex-shrink: 0;
}}

.avatar.me {{
    background: linear-gradient(135deg, #4ECDC4, #44B09E);
}}

.avatar.friend {{
    background: linear-gradient(135deg, #FF6B6B, #EE5A24);
}}

.msg-bubble {{
    max-width: 280px;
    padding: 10px 14px;
    border-radius: 8px;
    font-size: 15px;
    line-height: 1.5;
    word-break: break-word;
    position: relative;
}}

.msg-bubble.me {{
    background: #95EC69;
    color: #000;
    border-top-right-radius: 2px;
}}

.msg-bubble.friend {{
    background: #fff;
    color: #000;
    border-top-left-radius: 2px;
    box-shadow: 0 1px 2px rgba(0,0,0,0.06);
}}

.msg-content {{
    margin-bottom: 2px;
}}

.msg-time {{
    font-size: 11px;
    color: #999;
    text-align: right;
    margin-top: 4px;
}}

.msg-bubble.me .msg-time {{
    color: #5a8c3c;
}}

/* 响应式 */
@media (max-width: 520px) {{
    .chat-container {{ max-width: 100%; padding: 8px 6px 30px; }}
    .msg-bubble {{ max-width: 240px; }}
}}
</style>
</head>
<body>
<div class="chat-header">
    {html_lib.escape(friend_name)}
    <div class="subtitle">共 {len(messages)} 条消息</div>
</div>
<div class="chat-container">
{"".join(bubbles)}
</div>
</body>
</html>'''
    
    with open(path, "w", encoding="utf-8") as f:
        f.write(html_content)
    
    return path


if __name__ == "__main__":
    print("请通过 wechat_analyzer.py 主入口运行。")
