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
# Твоя вечная сессия уже вшита сюда:
MY_SESSION_STRING = '1ApWapzMBu6a2yrYGwEl4SmIajfYwWFcdt93DPZJADeUU4mA61FcGqC9v_PqjQZm0zMQC3OZFXKLQzM_3_D15YlGyk4Z4s64oPq_dF2FXIW67-dTreso3mfFl2v3BILmO_PKoR_iBMZ5aYCUM_DY9rJcWA2_xhQ1RSmUc1HxzD9L1aDF7fiHAWcLiduwJFSOYDSuWTINIXPIIMsmqtxGxeNFM2sbgWJIFkBhGe0I4g_YaSlcV342H53kS0JUJrS2IGaTI6KgqQ6XymA9MdtjjjHRWiqb4xLRTBqyXgDvAFnnsnbegH8nMEkwudAyEa-Y-O5oCP4WJfS220InB3tNJFe8u9_qXbJw='

AVATAR_DIR = "avatars"
LIMIT_FILE = "usage_limit.json"
MAX_DAILY_PARSES = 50

if not os.path.exists(AVATAR_DIR): 
    os.makedirs(AVATAR_DIR)

st.set_page_config(page_title="VM Models | Premium Scout", layout="wide")

# --- PREMIUM UI (БРЕНДИНГ) ---
st.markdown(f"""
    <style>
    .stApp {{ background-color: #050505; color: #FFFFFF; }}
    
    /* Логотип VM Models */
    .logo-box {{ text-align: center; padding: 30px 0; }}
    .vm-text {{ color: #007BFF; font-size: 60px; font-weight: 900; font-family: 'Arial Black'; text-shadow: 0 0 15px rgba(0,123,255,0.4); }}
    .models-text {{ color: #FFFFFF; font-size: 60px; font-weight: 900; font-family: 'Arial Black'; }}
    
    /* Стилизация контейнеров */
    .stFieldBlock {{
        background: #111111;
        padding: 20px;
        border-radius: 15px;
        border: 1px solid #222;
        margin-bottom: 20px;
    }}
    
    /* Фирменная синяя кнопка */
    div.stButton > button {{
        background: linear-gradient(135deg, #007BFF 0%, #004080 100%);
        color: white; border: none; border-radius: 10px;
        padding: 18px; font-size: 18px; font-weight: bold;
        text-transform: uppercase; transition: 0.3s; width: 100%;
    }}
    div.stButton > button:hover {{ transform: translateY(-2px); box-shadow: 0 8px 20px rgba(0,123,255,0.3); color: white; }}
    
    /* Ввод данных */
    .stTextInput input, .stSelectbox div {{
        background-color: #1a1a1a !important; border: 1px solid #333 !important; 
        color: white !important; border-radius: 8px !important;
    }}
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

def inc_usage():
    data = get_usage()
    data["count"] += 1
    with open(LIMIT_FILE, "w") as f: json.dump(data, f)

async def run_parser(target, days, limit, method):
    client = TelegramClient(StringSession(MY_SESSION_STRING), API_ID, API_HASH)
    await client.connect()
    results, seen = [], set()

    async def process(u):
        if not u or u.id in seen or getattr(u, 'bot', False): return
        seen.add(u.id)
        path = "https://flaticon.com"
        if u.photo:
            p_name = f"{AVATAR_DIR}/{u.id}.jpg"
            if not os.path.exists(p_name):
                try: await client.download_profile_photo(u, file=p_name)
                except: pass
            if os.path.exists(p_name): path = p_name
        un = u.username or ""
        results.append({
            "Фото": path,
            "Имя": f"{u.first_name or ''} {u.last_name or ''}".strip() or "Скрыт",
            "Юзернейм": f"@{un}" if un else "---",
            "Открыть": f"tg://resolve?domain={un}" if un else f"tg://user?id={u.id}"
        })

    try:
        if "Все" in method:
            alphabet = "abcdefghijklmnopqrstuvwxyz0123456789"
            p_bar = st.progress(0)
            for i, char in enumerate(alphabet):
                p_bar.progress((i + 1) / len(alphabet))
                try:
                    res = await client(functions.channels.GetParticipantsRequest(
                        channel=target, filter=types.ChannelParticipantsSearch(char),
                        offset=0, limit=1000, hash=0
                    ))
                    for u in res.users: await process(u)
                except: continue
            p_bar.empty()
        else:
            limit_date = datetime.now(timezone.utc) - timedelta(days=days)
            async for m in client.iter_messages(target, limit=limit):
                if m.date < limit_date: break
                if m.sender_id: await process(await m.get_sender())
    finally: await client.disconnect()
    return results

# --- ИНТЕРФЕЙС ---
if 'auth' not in st.session_state: st.session_state.auth = False

if not st.session_state.auth:
    st.markdown('<div class="logo-box"><span class="vm-text">VM</span> <span class="models-text">Models</span></div>', unsafe_allow_html=True)
    c1, c2, c3 = st.columns([1,1.2,1])
    with c2:
        with st.form("login_ui"):
            u = st.text_input("Логин")
            p = st.text_input("Пароль", type="password")
            if st.form_submit_button("ВОЙТИ В ПАНЕЛЬ"):
                if u == "Admin.Maksym" and p == "Maksym777":
                    st.session_state.auth = True
                    st.rerun()
                else: st.error("Ошибка доступа")
else:
    st.markdown('<div class="logo-box" style="padding:10px 0;"><span class="vm-text" style="font-size:35px;">VM</span> <span class="models-text" style="font-size:35px;">Models</span></div>', unsafe_allow_html=True)
    
    usage = get_usage()
    with st.sidebar:
        st.markdown("### 📊 Лимиты")
        st.write(f"Сегодня: **{usage['count']} / {MAX_DAILY_PARSES}**")
        st.progress(usage['count'] / MAX_DAILY_PARSES)
        if st.button("Выйти"):
            st.session_state.auth = False
            st.rerun()

    tabs = st.tabs(["⚡️ СБОР", "📂 ИСТОРИЯ", "👥 КОМАНДА"])
    
    with tabs[0]:
        st.markdown('<div class="stFieldBlock">', unsafe_allow_html=True)
        col_1, col_2 = st.columns(2)
        with col_1:
            method = st.radio("Метод:", ["Все участники (Глубокий)", "Активные по периоду"])
            target = st.text_input("Ссылка на группу (напр. poehalisnami_de)")
        with col_2:
            if "Активные" in method:
                period = st.selectbox("Период активности:", ["3 дня", "Неделя", "Месяц", "3 месяца"])
                p_map = {"3 дня": 3, "Неделя": 7, "Месяц": 30, "3 месяца": 90}
                days_val = p_map[period]
                limit_val = 2000
            else: days_val, limit_val = 0, 0
        st.markdown('</div>', unsafe_allow_html=True)

        if st.button("🚀 ЗАПУСТИТЬ ПАРСИНГ"):
            if usage['count'] >= MAX_DAILY_PARSES: st.error("Дневной лимит (50) исчерпан")
            elif not target: st.warning("Укажите ссылку на группу")
            else:
                with st.spinner('VM Models Scout в работе...'):
                    try:
                        loop = asyncio.get_event_loop()
                    except:
                        loop = asyncio.new_event_loop()
                        asyncio.set_event_loop(loop)
                    
                    data = loop.run_until_complete(run_parser(target, days_val, limit_val, method))
                    if data:
                        inc_usage()
                        df = pd.DataFrame(data)
                        st.success(f"Найдено: {len(df)}")
                        st.dataframe(df, column_config={
                            "Фото": st.column_config.ImageColumn(),
                            "Открыть": st.column_config.LinkColumn("Чат")
                        }, use_container_width=True)
                        st.download_button("📥 Скачать CSV", df.to_csv(index=False).encode('utf-8'), "vm_scout.csv")

    with tabs[1]:
        st.info("История будет доступна в следующем обновлении (требуется база данных).")

    with tabs[2]:
        st.write("👤 **Admin.Maksym** (Админ)")
        st.write("👤 **Worker1** (Работник)")

