import os
import json
import streamlit as st
from openai import OpenAI
from dotenv import load_dotenv
from datetime import datetime

# ==== 1. 兼容本地和云端的密钥读取 ====
load_dotenv()
api_key = os.getenv("DEEPSEEK_API_KEY")

if not api_key:
    try:
        api_key = st.secrets["DEEPSEEK_API_KEY"]
    except:
        pass

# ==== 2. 网页界面设置 ====
st.set_page_config(page_title="AI 待办提取器", page_icon="📅")
st.title("📅 AI 通知提取器")
st.write("把 QQ、微信里杂乱的群通知粘贴到下面，AI 帮你提取任务并生成日历！")

notice_text = st.text_area("在此粘贴通知内容：", height=150)

if st.button("开始提取并生成日历"):
    if not notice_text:
        st.warning("请先粘贴一段通知内容哦！")
    else:
        with st.spinner("AI 正在疯狂提取中，请稍候..."):
            client = OpenAI(api_key=api_key, base_url="https://api.deepseek.com")
            today_str = datetime.now().strftime("%Y-%m-%d")
            
            try:
                response = client.chat.completions.create(
                    model="deepseek-chat",
                    messages=[
                        {"role": "system", "content": f"你是一个高效的助理。今天是 {today_str}。请帮我总结以下通知，提取出摘要、截止时间、待办任务。请务必输出严格的 JSON，格式要求：{{\"summary\": \"摘要\", \"tasks\": [{{\"task_name\": \"任务名\", \"event_date\": \"YYYYMMDD\", \"event_time\": \"HHMMSS\"}}]}}。注意：请你根据通知内容自己推算并填入正确的日期和时间格式（24小时制）。"},
                        {"role": "user", "content": notice_text}
                    ]
                )
                
                ai_reply = response.choices[0].message.content
                clean_json = ai_reply.replace("```json", "").replace("```", "").strip()
                data = json.loads(clean_json)
                
                st.success("提取成功！")
                st.write(f"**摘要：** {data.get('summary', '无')}")
                
                ics_content = [
                    "BEGIN:VCALENDAR", "VERSION:2.0", "PRODID:-//AI Notice Assistant//CN", "CALSCALE:GREGORIAN"
                ]
                
                tasks = data.get("tasks", [])
                for task in tasks:
                    st.write(f"- 任务：{task.get('task_name')} | 时间：{task.get('event_date')} {task.get('event_time')}")
                    
                    ics_content.extend([
                        "BEGIN:VEVENT",
                        f"SUMMARY:{task.get('task_name')}",
                        f"DTSTART:{task.get('event_date')}T{task.get('event_time')}",
                        f"DTEND:{task.get('event_date')}T{task.get('event_time')}",
                        "BEGIN:VALARM", "TRIGGER:-PT15M", "ACTION:DISPLAY", "DESCRIPTION:Reminder", "END:VALARM",
                        "END:VEVENT"
                    ])
                    
                ics_content.append("END:VCALENDAR")
                final_ics = "\n".join(ics_content)
                
                st.download_button(
                    label="⬇️ 点击下载日历文件 (.ics)",
                    data=final_ics,
                    file_name="my_tasks.ics",
                    mime="text/calendar"
                )
                
            except Exception as e:
                st.error(f"出错了：{e}")