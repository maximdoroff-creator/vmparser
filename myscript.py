import streamlit as st
import asyncio
import pandas as pd
import os
import json
from telethon import TelegramClient, functions, types
from telethon.sessions import StringSession
from datetime import datetime, timedelta, timezone

# --- КОНФИГУРАЦИЯ ---
API_ID = 34321415 
API_HASH = 'a858399e90e04f5992a97096b614f31e'
MY_SESSION_STRING = '1ApWapzMBu6a2yrYGwEl4SmIajfYwWFcdt93DPZJADeUU4mA61FcGqC9v_PqjQZm0zMQC3OZFXKLQzM_3_D15YlGyk4Z4s64oPq_dF2FXIW67-dTreso3mfFl2v3BILmO_PKoR_iBMZ5aYCUM_DY9rJcWA2_xhQ1RSmUc1HxzD9L1aDF7fiHAWcLiduwJFSOYDSuWTINIXPIIMsmqtxGxeNFM2sbgWJIFkBhGe0I4g_YaSlcV342H53kS0JUJrS2IGaTI6KgqQ6XymA9MdtjjjHRWiqb4xLRTBqyXgDvAFnnsnbegH8nMEkwudAyEa-Y-O5oCP4WJfS220InB3tNJFe8u9_qXbJw='

LIMIT_FILE = "usage_limit.json"
MAX_DAILY_PARSES = 50

st.set_page_config(page_title="VM Models | Pro Scout", layout="wide")

# --- ULTIMATE DARK UI ---
st.markdown(f"""
    <style>
    .stApp {{ background-color: #000000; color: #FFFFFF; }}
    
    /* Логотип */
    .logo-box {{ text-align: center; padding: 20px 0; margin-bottom: 20px; }}
    .vm-text {{ color: #007BFF; font-size: 50px; font-weight: 900; font-family: 'Arial Black'; }}
    .models-text {{ color: #FFFFFF; font-size: 50px; font-weight: 900; font-family: 'Arial Black'; }}
    
    /* Читаемость текста */
    label, p, .stMarkdown {{ color: #FFFFFF !important; font-weight: 500 !important; font-size: 16px !important; }}
    .stRadio label {{ color: #FFFFFF !important; }}
    
    /* Кнопка */
    div.stButton > button {{
        background: linear-gradient(90deg, #007BFF 0%, #004080 100%);
        color: white; border-radius: 8px; padding: 15px; font-weight: bold; width: 100%; border: none;
    }}
    
    /* Поля ввода (убираем серый налет) */
    .stTextInput input, .stSelectbox div {{
        background-color: #000000 !important; border: 2px solid #333 !important; 
        color: white !important; border-radius: 8px !important;
    }}
    .stTextInput input:focus {{ border-color: #007BFF !important; }}
    
    /* Таблица */
    [data-testid="stTable"] {{ background-color: #000000; }}
    </style>
    """, unsafe_allow_html=True)

# --- ЛОГИКА ---
def get_usage():
    today = datetime.now().strftime("%Y-%m-%d")
    if not os.path.exists(LIMIT_FILE): return {"date": today, "count": 0}
    try:
        with open(LIMIT_FILE, "r") as f: data = json.load(f)
        return data if data["date"] == today else {"date": today, "count": 0}
    except: return {"date": today, "count": 0}

async def run_live_parser(target, days, limit, method, placeholder):
    client = TelegramClient(StringSession(MY_SESSION_STRING), API_ID, API_HASH)
    await client.connect()
    
    results, seen = [], set()
    table_st = st.empty() # Место для живой таблицы

    async def process(u):
        if not u or u.id in seen or getattr(u, 'bot', False): return
        seen.add(u.id)
        un = u.username or ""
        results.append({
            "Имя": f"{u.first_name or ''} {u.last_name or ''}".strip() or "User",
            "Username": f"@{un}" if un else "---",
            "Telegram": f"tg://resolve?domain={un}" if un else f"tg://user?id={u.id}"
        })
        # Сразу обновляем таблицу на экране
        table_st.dataframe(pd.DataFrame(results), column_config={"Telegram": st.column_config.LinkColumn()}, use_container_width=True)

    try:
        if "Все" in method:
            for char in "abcdefghijklmnopqrstuvwxyz0123456789":
                res = await client(functions.channels.GetParticipantsRequest(
                    channel=target, filter=types.ChannelParticipantsSearch(char),
                    offset=0, limit=1000, hash=0
                ))
                for u in res.users: await process(u)
        else:
            limit_date = datetime.now(timezone.utc) - timedelta(days=days)
            async for m in client.iter_messages(target, limit=limit):
                if m.date < limit_date: break
                if m.sender_id: await process(await m.get_sender())
    finally:
        await client.disconnect()
    return results

# --- ИНТЕРФЕЙС ---
if 'auth' not in st.session_state: st.session_state.auth = False

if not st.session_state.auth:
    st.markdown('<div class="logo-box"><span class="vm-text">VM</span> <span class="models-text">Models</span></div>', unsafe_allow_html=True)
    c1, c2, c3 = st.columns([1,1.2,1])
    with c2:
        u = st.text_input("Username")
        p = st.text_input("Password", type="password")
        if st.button("LOGIN"):
            if u == "Admin.Maksym" and p == "Maksym777":
                st.session_state.auth = True
                st.rerun()
else:
    st.markdown('<div class="logo-box"><span class="vm-text" style="font-size:40px;">VM</span> <span class="models-text" style="font-size:40px;">Models</span></div>', unsafe_allow_html=True)
    
    usage = get_usage()
    with st.sidebar:
        st.write(f"📊 Лимиты: **{usage['count']}/50**")
        if st.button("Logout"):
            st.session_state.auth = False
            st.rerun()

    method = st.radio("Выберите метод:", ["Активные (по сообщениям)", "Все участники (Глубокий)"], horizontal=True)
    target = st.text_input("Ссылка на группу (напр. nakordoni_poland)")
    
    if "Активные" in method:
        period = st.selectbox("За какой срок искать?", ["3 дня", "Неделя", "Месяц"])
        p_map = {"3 дня": 3, "Неделя": 7, "Месяц": 30}
        days_val = p_map[period]
    else: days_val = 0

    if st.button("🚀 ЗАПУСТИТЬ ПОИСК"):
        if not target: st.warning("Введите ссылку!")
        else:
            status = st.empty()
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            final_data = loop.run_until_complete(run_live_parser(target, days_val, 1500, method, status))
            
            if final_data:
                st.success(f"Поиск завершен! Найдено: {len(final_data)}")
                csv = pd.DataFrame(final_data).to_csv(index=False).encode('utf-8')
                st.download_button("📥 СКАЧАТЬ РЕЗУЛЬТАТ", csv, "vm_export.csv")


