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
DB_FILE = "users_db.json"

st.set_page_config(page_title="VM Models | System", layout="wide")

# --- ЛОГИКА БАЗЫ ДАННЫХ ---
def load_db():
    if not os.path.exists(DB_FILE):
        # Твой основной доступ зашит здесь изначально
        return [{"login": "Admin.Maksym", "pass": "Maksym777", "role": "Админ", "session": ""}]
    with open(DB_FILE, "r") as f:
        return json.load(f)

def save_db(data):
    with open(DB_FILE, "w") as f:
        json.dump(data, f)

if 'users' not in st.session_state:
    st.session_state.users = load_db()

# --- УЛУЧШЕННЫЙ ДИЗАЙН (МАКСИМАЛЬНАЯ ЧИТАЕМОСТЬ) ---
st.markdown("""
    <style>
    /* Фон и базовый текст */
    .stApp { background-color: #000000; color: #FFFFFF !important; }
    
    /* Делаем все надписи ярко-белыми */
    label, p, span, .stMarkdown, .stSubheader, h1, h2, h3 { 
        color: #FFFFFF !important; 
        font-weight: 600 !important; 
    }
    
    /* Логотип */
    .brand-vm { color: #007BFF; font-size: 42px; font-weight: 900; font-family: 'Arial Black'; }
    .brand-models { color: #FFFFFF; font-size: 42px; font-weight: 900; }
    
    /* Поля ввода (делаем их контрастными) */
    .stTextInput input, .stSelectbox div {
        background-color: #111111 !important;
        border: 2px solid #333333 !important;
        color: #FFFFFF !important;
        border-radius: 8px !important;
    }
    .stTextInput input:focus { border-color: #007BFF !important; }

    /* Кнопки */
    div.stButton > button {
        background: linear-gradient(90deg, #007BFF 0%, #0056b3 100%) !important;
        color: white !important;
        border-radius: 12px !important;
        border: none !important;
        padding: 15px 30px !important;
        font-weight: bold !important;
        text-transform: uppercase;
    }
    
    /* Таблица */
    [data-testid="stDataFrame"] { background-color: #000000 !important; }
    </style>
    """, unsafe_allow_html=True)

# --- ЛОГИКА ПАРСЕРА ---
async def run_live_parser(user_session, target, method, placeholder):
    main_key = '1ApWapzMBu6a2yrYGwEl4SmIajfYwWFcdt93DPZJADeUU4mA61FcGqC9v_PqjQZm0zMQC3OZFXKLQzM_3_D15YlGyk4Z4s64oPq_dF2FXIW67-dTreso3mfFl2v3BILmO_PKoR_iBMZ5aYCUM_DY9rJcWA2_xhQ1RSmUc1HxzD9L1aDF7fiHAWcLiduwJFSOYDSuWTINIXPIIMsmqtxGxeNFM2sbgWJIFkBhGe0I4g_YaSlcV342H53kS0JUJrS2IGaTI6KgqQ6XymA9MdtjjjHRWiqb4xLRTBqyXgDvAFnnsnbegH8nMEkwudAyEa-Y-O5oCP4WJfS220InB3tNJFe8u9_qXbJw='
    final_key = user_session if user_session else main_key
    
    client = TelegramClient(StringSession(final_key), API_ID, API_HASH)
    await client.connect()
    results, seen = [], set()

    async def process(u):
        if not u or u.id in seen or getattr(u, 'bot', False): return
        seen.add(u.id)
        un = u.username or ""
        results.append({
            "ИМЯ": f"{u.first_name or ''} {u.last_name or ''}".strip(),
            "ЮЗЕРНЕЙМ": f"@{un}" if un else "---",
            "СВЯЗЬ": f"tg://resolve?domain={un}" if un else f"tg://user?id={u.id}"
        })
        placeholder.dataframe(pd.DataFrame(results), column_config={"СВЯЗЬ": st.column_config.LinkColumn("ЧАТ 🔵")}, use_container_width=True, hide_index=True)

    try:
        if "Все" in method:
            for char in "abcdefghijklmnopqrstuvwxyz":
                res = await client(functions.channels.GetParticipantsRequest(channel=target, filter=types.ChannelParticipantsSearch(char), offset=0, limit=1000, hash=0))
                for u in res.users: await process(u)
        else:
            async for m in client.iter_messages(target, limit=1500):
                if m.sender_id: await process(await m.get_sender())
    finally: await client.disconnect()
    return results

# --- ЭКРАН ВХОДА ---
if 'auth' not in st.session_state: st.session_state.auth = False

if not st.session_state.auth:
    st.markdown('<div style="text-align:center; padding-top:100px;"><span class="brand-vm">VM</span> <span class="brand-models">Models</span></div>', unsafe_allow_html=True)
    c1, c2, c3 = st.columns([1, 1.3, 1])
    with c2:
        l = st.text_input("Логин")
        p = st.text_input("Пароль", type="password")
        if st.button("ВОЙТИ"):
            user = next((x for x in st.session_state.users if x["login"] == l and x["pass"] == p), None)
            if user:
                st.session_state.auth = True
                st.session_state.user_data = user
                st.rerun()
            else: st.error("Неверный доступ")
else:
    # --- ГЛАВНОЕ МЕНЮ ---
    st.markdown(f'<div style="display:flex; justify-content:space-between; padding:10px 0; border-bottom:1px solid #333; margin-bottom:20px;"><div class="brand-vm" style="font-size:24px;">VM <span class="brand-models" style="font-size:24px;">Models</span></div><div style="color:#007BFF;">{st.session_state.user_data["role"]}: {st.session_state.user_data["login"]}</div></div>', unsafe_allow_html=True)
    
    tabs = st.tabs(["⚡️ СБОР", "📖 ИНСТРУКЦИЯ", "👥 КОМАНДА"])

    with tabs[0]:
        target = st.text_input("Ссылка на группу", placeholder="nakordoni_poland")
        method = st.radio("Алгоритм:", ["Все участники", "Активные за период"], horizontal=True)
        if st.button("🚀 ЗАПУСТИТЬ ПАРСИНГ"):
            if target:
                placeholder = st.empty()
                loop = asyncio.new_event_loop(); asyncio.set_event_loop(loop)
                loop.run_until_complete(run_live_parser(st.session_state.user_data.get("session", ""), target, method, placeholder))

    with tabs[1]:
        st.subheader("Инструкция для сотрудников 📲")
        st.write("Чтобы парсер работал от вашего имени, вставьте свой ключ (StringSession) ниже:")
        session_val = st.text_input("Ваш ключ:", value=st.session_state.user_data.get("session", ""))
        if st.button("Сохранить ключ"):
            for u in st.session_state.users:
                if u["login"] == st.session_state.user_data["login"]:
                    u["session"] = session_val
                    st.session_state.user_data["session"] = session_val
            save_db(st.session_state.users)
            st.success("Данные обновлены!")

    with tabs[2]:
        if st.session_state.user_data["role"] == "Админ":
            st.subheader("Управление командой")
            col_a, col_b = st.columns(2)
            with col_a:
                st.write("### Добавить сотрудника")
                nl = st.text_input("Новый Логин")
                np = st.text_input("Новый Пароль")
                if st.button("Создать"):
                    st.session_state.users.append({"login": nl, "pass": np, "role": "Работник", "session": ""})
                    save_db(st.session_state.users)
                    st.success("Добавлен!")
                    st.rerun()
            with col_b:
                st.write("### Текущий состав")
                for i, u in enumerate(st.session_state.users):
                    if u["role"] != "Админ":
                        c_n, c_d = st.columns([2, 1])
                        c_n.write(f"👤 {u['login']}")
                        if c_d.button("Удалить", key=f"d_{i}"):
                            st.session_state.users.pop(i)
                            save_db(st.session_state.users)
                            st.rerun()
    
    with st.sidebar:
        if st.button("ВЫХОД"):
            st.session_state.auth = False
            st.rerun()


