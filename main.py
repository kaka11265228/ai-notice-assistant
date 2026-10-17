import os
import json
import streamlit as st
from openai import OpenAI
from dotenv import load_dotenv
from datetime import datetime, timedelta

load_dotenv()
api_key = os.getenv("DEEPSEEK_API_KEY")
if not api_key:
    api_key = st.secrets
client = OpenAI(
    api_key=api_key,
    base_url="https://api.deepseek.com" 
)

# 测试通知，注意里面有明确的时间
notice_text = "今晚 8 点前，请各位同学把高数作业交到学习通，逾期不候。另外班长今晚 9 点在群里开会。"

# 为了让 AI 知道今天是哪天，我们把当前时间告诉它
today_str = datetime.now().strftime("%Y-%m-%d")
print(f"今天是：{today_str}")

print("正在呼叫 AI 大脑提取并生成日历格式...\n")

response = client.chat.completions.create(
    model="deepseek-chat",
    messages=[
        {"role": "system", "content": f"你是一个高效的助理。今天是 {today_str}。请帮我总结以下通知，提取出摘要、截止时间、待办任务。请务必输出严格的 JSON，格式要求：{{\"summary\": \"摘要\", \"tasks\": [{{\"task_name\": \"任务名\", \"event_date\": \"YYYYMMDD\", \"event_time\": \"HHMMSS\"}}]}}。注意：请你根据通知内容（比如今晚8点），自己推算并填入正确的日期和时间格式（24小时制）。"},
        {"role": "user", "content": notice_text}
    ]
)

ai_reply = response.choices[0].message.content
print("====== AI 的原始回复 ======")
print(ai_reply)

try:
    clean_json = ai_reply.replace("```json", "").replace("```", "").strip()
    data = json.loads(clean_json)
    
    # 开始生成 .ics 日历文件
    ics_content = [
        "BEGIN:VCALENDAR",
        "VERSION:2.0",
        "PRODID:-//AI Notice Assistant//CN",
        "CALSCALE:GREGORIAN"
    ]
    
    print("\n====== 生成日历事件中 ======")
    
    for task in data.get("tasks", []):
        task_name = task.get("task_name", "未知任务")
        event_date = task.get("event_date", "20261017") # 兜底日期
        event_time = task.get("event_time", "200000")   # 兜底时间
        
        print(f"- 提取到任务: {task_name} | 时间: {event_date} {event_time}")
        
        # 每一个任务在 .ics 里就是一个 VEVENT
        ics_content.extend([
            "BEGIN:VEVENT",
            f"SUMMARY:{task_name}",
            f"DTSTART:{event_date}T{event_time}",
            f"DTEND:{event_date}T{event_time}", # 这里为了简单，结束时间先设为和开始一样
            "BEGIN:VALARM",
            "TRIGGER:-PT15M", # 提前 15 分钟提醒
            "ACTION:DISPLAY",
            "DESCRIPTION:Reminder",
            "END:VALARM",
            "END:VEVENT"
        ])
        
    ics_content.append("END:VCALENDAR")
    
    # 把列表拼成字符串，并写入文件
    final_ics = "\n".join(ics_content)
    with open("my_tasks.ics", "w", encoding="utf-8") as f:
        f.write(final_ics)
        
    print("\n✅ 成功！已在左侧生成 my_tasks.ics 文件。请双击它导入到你的日历中！")
    
except Exception as e:
    print(f"\n❌ 出错了：{e}")