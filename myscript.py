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
# Твой основной ключ (запасной)
MY_SESSION_STRING = '1ApWapzMBu6a2yrYGwEl4SmIajfYwWFcdt93DPZJADeUU4mA61FcGqC9v_PqjQZm0zMQC3OZFXKLQzM_3_D15YlGyk4Z4s64oPq_dF2FXIW67-dTreso3mfFl2v3BILmO_PKoR_iBMZ5aYCUM_DY9rJcWA2_xhQ1RSmUc1HxzD9L1aDF7fiHAWcLiduwJFSOYDSuWTINIXPIIMsmqtxGxeNFM2sbgWJIFkBhGe0I4g_YaSlcV342H53kS0JUJrS2IGaTI6KgqQ6XymA9MdtjjjHRWiqb4xLRTBqyXgDvAFnnsnbegH8nMEkwudAyEa-Y-O5oCP4WJfS220InB3tNJFe8u9_qXbJw='

st.set_page_config(page_title="VM Models | Professional Scout System", layout="wide")

# --- БАЗА ДАННЫХ ---
def load_db():
    if not os.path.exists(DB_FILE):
        return [{"login": "Admin.Maksym", "pass": "Maksym777", "role": "Админ", "session": ""}]
    try:
        with open(DB_FILE, "r") as f: return json.load(f)
    except: return [{"login": "Admin.Maksym", "pass": "Maksym777", "role": "Админ", "session": ""}]

def save_db(data):
    with open(DB_FILE, "w") as f: json.dump(data, f)

if 'users' not in st.session_state:
    st.session_state.users = load_db()

# --- PREMIUM UI DESIGN (MODERN DASHBOARD) ---
st.markdown(f"""
    <style>
    .stApp {{ background-color: #0d111b; color: #ffffff; }}
    
    /* Хедер (Карточки сверху) */
    .stat-card {{
        background: #161b2c; border: 1px solid #232d45;
        border-radius: 12px; padding: 20px; margin-bottom: 20px;
    }}
    .stat-label {{ color: #8a8d9b; font-size: 12px; text-transform: uppercase; font-weight: bold; letter-spacing: 1px; }}
    .stat-value {{ color: #ffffff; font-size: 20px; font-weight: 900; margin-top: 8px; }}

    /* Логотип */
    .vm-blue {{ color: #007BFF; font-weight: 900; }}
    .models-white {{ color: #FFFFFF; font-weight: 900; }}

    /* Текст */
    label, p, .stMarkdown {{ color: #FFFFFF !important; font-weight: 500 !important; font-size: 15px !important; }}

    /* Кнопки */
    div.stButton > button {{
        background: linear-gradient(90deg, #007BFF 0%, #0056b3 100%);
        color: white !important; border-radius: 10px; border: none; font-weight: bold;
        padding: 12px; transition: 0.3s;
    }}
    div.stButton > button:hover {{ transform: translateY(-2px); box-shadow: 0 5px 15px rgba(0,123,255,0.4); }}
    
    /* Розовая кнопка Создать */
    .pink-btn button {{ background: linear-gradient(90deg, #eb4899 0%, #db2777 100%) !important; }}

    /* Стилизация табов */
    .stTabs [data-baseweb="tab-list"] {{ gap: 24px; }}
    .stTabs [aria-selected="true"] {{ color: #007BFF !important; border-bottom: 3px solid #007BFF !important; }}
    </style>
    """, unsafe_allow_html=True)

# --- ЛОГИКА ПАРСЕРА ---
async def run_live_parser(session_str, target, days, method, table_placeholder):
    # Приоритет: сессия сотрудника -> основная сессия
    final_session = session_str if session_str and len(session_str) > 50 else MY_SESSION_STRING
    client = TelegramClient(StringSession(final_session), API_ID, API_HASH)
    
    try:
        await client.connect()
        results, seen = [], set()

        async def process(u):
            if not u or u.id in seen or getattr(u, 'bot', False): return
            seen.add(u.id)
            un = u.username or ""
            results.append({
                "ИМЯ": f"{u.first_name or ''} {u.last_name or ''}".strip() or "User",
                "ЮЗЕРНЕЙМ": f"@{un}" if un else "---",
                "СВЯЗЬ": f"tg://resolve?domain={un}" if un else f"tg://user?id={u.id}"
            })
            table_placeholder.dataframe(
                pd.DataFrame(results), 
                column_config={
                    "СВЯЗЬ": st.column_config.LinkColumn("НАПИСАТЬ 🔵")
                }, 
                use_container_width=True, 
                hide_index=True
            )

        if "Все" in method:
            alphabet = "abcdefghijklmnopqrstuvwxyz0123456789"
            for char in alphabet:
                res = await client(functions.channels.GetParticipantsRequest(
                    channel=target, filter=types.ChannelParticipantsSearch(char), 
                    offset=0, limit=1000, hash=0
                ))
                for u in res.users: await process(u)
        else:
            limit_date = datetime.now(timezone.utc) - timedelta(days=days)
            async for m in client.iter_messages(target, limit=2000):
                if m.date < limit_date: break
                if m.sender_id: await process(await m.get_sender())
    except Exception as e:
        st.error(f"Ошибка подключения: {e}")
    finally:
        await client.disconnect()
    return results

# --- ИНТЕРФЕЙС ---
if 'auth' not in st.session_state: st.session_state.auth = False

if not st.session_state.auth:
    st.markdown('<div style="text-align:center; padding-top:100px; font-size:45px;"><span class="vm-blue">VM</span> <span class="models-white">Models</span></div>', unsafe_allow_html=True)
    c1, c2, c3 = st.columns([1, 1.2, 1])
    with c2:
        u_in = st.text_input("Username")
        p_in = st.text_input("Password", type="password")
        if st.button("ВХОД В СИСТЕМУ"):
            user = next((x for x in st.session_state.users if x["login"] == u_in and x["pass"] == p_in), None)
            if user:
                st.session_state.auth = True; st.session_state.user_data = user; st.rerun()
            else: st.error("Неверные учетные данные")
else:
    # --- DASHBOARD HEADER ---
    col_u, col_t, col_l = st.columns(3)
    with col_u:
        st.markdown(f'<div class="stat-card"><div class="stat-label">ПОЛЬЗОВАТЕЛЬ</div><div class="stat-value">{st.session_state.user_data["login"]}</div></div>', unsafe_allow_html=True)
    with col_t:
        st.markdown(f'<div class="stat-card"><div class="stat-label">TELEGRAM API</div><div class="stat-value" style="color:#3fb950;">ПОДКЛЮЧЕН ✔</div></div>', unsafe_allow_html=True)
    with col_l:
        st.markdown(f'<div class="stat-card"><div class="stat-label">ЛИМИТ ПАРСИНГА (ДЕНЬ)</div><div class="stat-value">12 / 50</div><div style="background:#232d45; height:6px; border-radius:3px; margin-top:10px;"><div style="background:#007BFF; width:24%; height:6px; border-radius:3px;"></div></div></div>', unsafe_allow_html=True)

    # --- ГЛАВНОЕ МЕНЮ ---
    tabs = st.tabs(["📖 ИНСТРУКЦИЯ", "📦 СБОР КОНТАКТОВ", "📂 ИСТОРИЯ", "👥 КОМАНДА", "❓ ПОМОЩЬ"])

    with tabs[0]: # ИНСТРУКЦИЯ
        st.markdown("""
        ### Добро пожаловать в VM Models Scout 🚀
        Здесь вы можете собирать целевую аудиторию из любых Telegram групп. 
        1. Перейдите во вкладку **СБОР**.
        2. Вставьте ссылку на группу.
        3. Выберите метод и период активности.
        4. Получите список контактов и переходите к рассылке.
        """)

    with tabs[1]: # СБОР
        st.markdown('<div style="background:#161b2c; padding:30px; border-radius:15px; border:1px solid #232d45;">', unsafe_allow_html=True)
        target = st.text_input("Ссылка на целевой чат", placeholder="https://t.me")
        col_m, col_p = st.columns(2)
        with col_m:
            method = st.radio("Алгоритм сбора:", ["Все участники (Глубокий)", "Активные за период"], horizontal=True)
        with col_p:
            if "Активные" in method:
                period = st.selectbox("Период активности сообщений:", ["3 дня", "7 дней", "Месяц", "3 месяца"])
                p_map = {"3 дня": 3, "7 дней": 7, "Месяц": 30, "3 месяца": 90}
                days_val = p_map[period]
            else: days_val = 0
            
        if st.button("🚀 ЗАПУСТИТЬ СКАУТИНГ"):
            if target:
                table_placeholder = st.empty()
                loop = asyncio.new_event_loop(); asyncio.set_event_loop(loop)
                loop.run_until_complete(run_live_parser(st.session_state.user_data.get("session", ""), target, days_val, method, table_placeholder))
            else: st.warning("Пожалуйста, укажите ссылку на группу!")
        st.markdown('</div>', unsafe_allow_html=True)

    with tabs[3]: # КОМАНДА
        if st.session_state.user_data["role"] == "Админ":
            col_add, col_list = st.columns([1, 2])
            with col_add:
                st.subheader("Добавить в команду")
                nl = st.text_input("Логин сотрудника")
                np = st.text_input("Пароль сотрудника")
                st.markdown('<div class="pink-btn">', unsafe_allow_html=True)
                if st.button("Создать доступ"):
                    st.session_state.users.append({"login": nl, "pass": np, "role": "Работник", "session": ""})
                    save_db(st.session_state.users); st.rerun()
                st.markdown('</div>', unsafe_allow_html=True)
            with col_list:
                st.subheader("Структура команды")
                for i, u in enumerate(st.session_state.users):
                    if u["role"] != "Админ":
                        c_n, c_b = st.columns([3, 1])
                        c_n.markdown(f'<div style="padding:10px; background:#1c223a; border-radius:8px; margin-bottom:5px;">👤 <b>{u["login"]}</b> (Скаут)</div>', unsafe_allow_html=True)
                        if c_b.button("Удалить", key=f"del_user_{i}"):
                            st.session_state.users.pop(i); save_db(st.session_state.users); st.rerun()
        else: st.warning("Доступ к управлению командой есть только у Администратора.")

    with tabs[4]: # ПОМОЩЬ
        st.markdown("""
        ### Инструкция для персонала 📲
        Чтобы парсер работал от вашего личного аккаунта:
        1. Получите у Администратора скрипт `get_session.py`.
        2. Запустите его на своем ПК и авторизуйтесь.
        3. Полученную строку-ключ (StringSession) вставьте в поле ниже:
        """)
        current_sess = st.text_input("Ваш персональный ключ Telegram:", value=st.session_state.user_data.get("session", ""))
        if st.button("Сохранить мой ключ"):
            for u in st.session_state.users:
                if u["login"] == st.session_state.user_data["login"]:
                    u["session"] = current_sess
                    st.session_state.user_data["session"] = current_sess
            save_db(st.session_state.users); st.success("Настройки успешно сохранены!")

    with st.sidebar:
        st.markdown('<div style="font-size:24px; margin-bottom:20px;"><span class="vm-blue">VM</span> <span class="models-white">Models</span></div>', unsafe_allow_html=True)
        if st.button("Выход из системы"):
            st.session_state.auth = False; st.rerun()

