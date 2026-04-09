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
DB_FILE = "users_data.json" # Файл для хранения сотрудников

st.set_page_config(page_title="VM Models | Team Management", layout="wide")

# --- СИСТЕМА ПОЛЬЗОВАТЕЛЕЙ (БАЗА ДАННЫХ) ---
def load_users():
    if not os.path.exists(DB_FILE):
        # Начальный список, если файла нет
        return [{"login": "Admin.Maksym", "pass": "Maksym777", "role": "Админ", "session": ""}]
    with open(DB_FILE, "r") as f:
        return json.load(f)

def save_users(users):
    with open(DB_FILE, "w") as f:
        json.dump(users, f)

if 'users_db' not in st.session_state:
    st.session_state.users_db = load_users()

# --- ДИЗАЙН VM MODELS BLUE ---
st.markdown("""
    <style>
    .stApp { background-color: #080a12; color: #ffffff; }
    .brand-vm { color: #007BFF; font-size: 32px; font-weight: 900; font-family: 'Arial Black'; }
    .brand-models { color: #ffffff; font-size: 32px; font-weight: 900; }
    .info-card { background: #101425; border-radius: 12px; padding: 20px; border: 1px solid #1c223a; margin-bottom: 15px; }
    div.stButton > button {
        background: linear-gradient(90deg, #007BFF 0%, #0056b3 100%) !important;
        color: white !important; border-radius: 10px !important; border: none !important;
        padding: 12px 25px !important; font-weight: bold !important;
    }
    .stTabs [aria-selected="true"] { color: #007BFF !important; border-bottom-color: #007BFF !important; }
    </style>
    """, unsafe_allow_html=True)

# --- ЛОГИКА ПАРСЕРА ---
async def run_live_parser(session_str, target, days, method, placeholder):
    # Если у сотрудника нет своей сессии, берем общую (твою)
    final_session = session_str if session_str else '1ApWapzMBu6a2yrYGwEl4SmIajfYwWFcdt93DPZJADeUU4mA61FcGqC9v_PqjQZm0zMQC3OZFXKLQzM_3_D15YlGyk4Z4s64oPq_dF2FXIW67-dTreso3mfFl2v3BILmO_PKoR_iBMZ5aYCUM_DY9rJcWA2_xhQ1RSmUc1HxzD9L1aDF7fiHAWcLiduwJFSOYDSuWTINIXPIIMsmqtxGxeNFM2sbgWJIFkBhGe0I4g_YaSlcV342H53kS0JUJrS2IGaTI6KgqQ6XymA9MdtjjjHRWiqb4xLRTBqyXgDvAFnnsnbegH8nMEkwudAyEa-Y-O5oCP4WJfS220InB3tNJFe8u9_qXbJw='
    
    client = TelegramClient(StringSession(final_session), API_ID, API_HASH)
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
        placeholder.dataframe(pd.DataFrame(results), column_config={"СВЯЗЬ": st.column_config.LinkColumn("НАПИСАТЬ 🔵")}, use_container_width=True, hide_index=True)

    try:
        if "Все" in method:
            for char in "abcdefghijklmnopqrstuvwxyz":
                res = await client(functions.channels.GetParticipantsRequest(channel=target, filter=types.ChannelParticipantsSearch(char), offset=0, limit=1000, hash=0))
                for u in res.users: await process(u)
        else:
            limit_date = datetime.now(timezone.utc) - timedelta(days=days)
            async for m in client.iter_messages(target, limit=1500):
                if m.date < limit_date: break
                if m.sender_id: await process(await m.get_sender())
    finally: await client.disconnect()
    return results

# --- ИНТЕРФЕЙС ---
if 'auth' not in st.session_state: st.session_state.auth = False

if not st.session_state.auth:
    st.markdown('<div style="text-align:center; padding-top:100px;"><span class="brand-vm">VM</span> <span class="brand-models">Models</span></div>', unsafe_allow_html=True)
    c1, c2, c3 = st.columns([1, 1.2, 1])
    with c2:
        u = st.text_input("Логин")
        p = st.text_input("Пароль", type="password")
        if st.button("ВОЙТИ"):
            user = next((x for x in st.session_state.users_db if x["login"] == u and x["pass"] == p), None)
            if user:
                st.session_state.auth = True
                st.session_state.user_data = user
                st.rerun()
            else: st.error("Ошибка доступа")
else:
    st.markdown(f'<div style="display:flex; justify-content:space-between; align-items:center; padding:10px 0; border-bottom:1px solid #1c223a; margin-bottom:20px;"><div class="brand-vm">VM <span class="brand-models">Models</span></div><div style="color:#58a6ff;">{st.session_state.user_data["role"]}: {st.session_state.user_data["login"]}</div></div>', unsafe_allow_html=True)
    
    tabs = st.tabs(["📖 ИНСТРУКЦИЯ", "📦 СБОР", "👥 КОМАНДА"])

    # --- ВКЛАДКА 1: ИНСТРУКЦИЯ ---
    with tabs[0]:
        st.subheader("Как настроить парсер для работы 🚀")
        col_text, col_img = st.columns([2, 1])
        with col_text:
            st.markdown("""
            ### Для сотрудников:
            Чтобы парсер работал стабильно и не вылетал, вам нужно подключить свою **Telegram сессию**:
            1. Запустите на своем компьютере скрипт `get_session.py` (возьмите у админа).
            2. Введите свой номер и код из Telegram.
            3. Полученную длинную строку вставьте в поле ниже и нажмите **"Сохранить сессию"**.
            
            *Это позволит вам парсить группы от своего имени, не мешая остальным.*
            """)
            current_session = st.text_input("Ваша StringSession (текстовый ключ):", value=st.session_state.user_data.get("session", ""))
            if st.button("Сохранить сессию"):
                for u in st.session_state.users_db:
                    if u["login"] == st.session_state.user_data["login"]:
                        u["session"] = current_session
                        st.session_state.user_data["session"] = current_session
                save_users(st.session_state.users_db)
                st.success("Сессия сохранена! Теперь парсинг будет идти через ваш аккаунт.")
        
        with col_img:
            st.info("💡 **Совет:** Используйте отдельные аккаунты для парсинга, чтобы не нагружать основной профиль.")

    # --- ВКЛАДКА 2: СБОР ---
    with tabs[1]:
        st.markdown('<div class="info-card">', unsafe_allow_html=True)
        target = st.text_input("Ссылка на группу", placeholder="nakordoni_poland")
        method = st.radio("Алгоритм:", ["Активные (неделя)", "Все участники"], horizontal=True)
        if st.button("🚀 ЗАПУСТИТЬ ПАРСИНГ"):
            if target:
                placeholder = st.empty()
                loop = asyncio.new_event_loop(); asyncio.set_event_loop(loop)
                loop.run_until_complete(run_live_parser(st.session_state.user_data.get("session", ""), target, 7, method, placeholder))
            else: st.warning("Укажите группу!")
        st.markdown('</div>', unsafe_allow_html=True)

    # --- ВКЛАДКА 3: КОМАНДА (ТОЛЬКО АДМИН) ---
    with tabs[2]:
        if st.session_state.user_data["role"] == "Админ":
            st.subheader("Управление доступом")
            
            # Форма добавления
            with st.expander("+ Добавить нового сотрудника"):
                new_login = st.text_input("Логин сотрудника")
                new_pass = st.text_input("Пароль сотрудника")
                if st.button("Создать аккаунт"):
                    if not any(u["login"] == new_login for u in st.session_state.users_db):
                        st.session_state.users_db.append({"login": new_login, "pass": new_pass, "role": "Работник", "session": ""})
                        save_users(st.session_state.users_db)
                        st.success(f"Сотрудник {new_login} добавлен!")
                        st.rerun()
                    else: st.error("Такой логин уже есть!")

            st.write("---")
            st.subheader("Список команды")
            for i, user in enumerate(st.session_state.users_db):
                col_name, col_role, col_btn = st.columns([2, 1, 1])
                col_name.write(f"👤 **{user['login']}**")
                col_role.write(f"({user['role']})")
                if user["role"] != "Админ":
                    if col_btn.button("Удалить доступ", key=f"del_{i}"):
                        st.session_state.users_db.pop(i)
                        save_users(st.session_state.users_db)
                        st.warning("Доступ удален")
                        st.rerun()
        else:
            st.warning("Доступ к управлению командой есть только у Администратора.")

    with st.sidebar:
        if st.button("Выйти из системы"):
            st.session_state.auth = False
            st.rerun()

