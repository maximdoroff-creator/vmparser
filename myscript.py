import streamlit as st
import asyncio
import pandas as pd
import os
import json
from telethon import TelegramClient, functions, types
from telethon.sessions import StringSession
from datetime import datetime, timedelta, timezone

# --- КОНФИГУРАЦИЯ ---
API_ID_DEFAULT = 34321415 
API_HASH_DEFAULT = 'a858399e90e04f5992a97096b614f31e'
DB_FILE = "vm_database.json"
# ТВОЯ СЕССИЯ
ADMIN_SESSION = '1ApWapzMBu6a2yrYGwEl4SmIajfYwWFcdt93DPZJADeUU4mA61FcGqC9v_PqjQZm0zMQC3OZFXKLQzM_3_D15YlGyk4Z4s64oPq_dF2FXIW67-dTreso3mfFl2v3BILmO_PKoR_iBMZ5aYCUM_DY9rJcWA2_xhQ1RSmUc1HxzD9L1aDF7fiHAWcLiduwJFSOYDSuWTINIXPIIMsmqtxGxeNFM2sbgWJIFkBhGe0I4g_YaSlcV342H53kS0JUJrS2IGaTI6KgqQ6XymA9MdtjjjHRWiqb4xLRTBqyXgDvAFnnsnbegH8nMEkwudAyEa-Y-O5oCP4WJfS220InB3tNJFe8u9_qXbJw='

st.set_page_config(page_title="VM Models | Enterprise Pro", layout="wide")

# --- БАЗА ДАННЫХ ---
def load_db():
    if not os.path.exists(DB_FILE):
        return {
            "users": [{"login": "Admin.Maksym", "pass": "Maksym777", "role": "Админ", "session": ADMIN_SESSION, "tg_name": "@Maksym_Admin", "limit": 0}],
            "history": []
        }
    try:
        with open(DB_FILE, "r", encoding="utf-8") as f: return json.load(f)
    except: return {"users": [{"login": "Admin.Maksym", "pass": "Maksym777", "role": "Админ", "session": ADMIN_SESSION, "tg_name": "@Maksym_Admin", "limit": 0}], "history": []}

def save_db(db):
    with open(DB_FILE, "w", encoding="utf-8") as f: json.dump(db, f, indent=4, ensure_ascii=False)

if 'db' not in st.session_state: st.session_state.db = load_db()
if 'auth' not in st.session_state: st.session_state.auth = False
if 'user' not in st.session_state: st.session_state.user = None

# --- PREMIUM UI ---
st.markdown("""
    <style>
    .stApp { background-color: #0d111b; color: #ffffff; }
    .vm-blue { color: #007BFF; font-weight: 900; font-size: 30px; font-family: 'Arial Black'; }
    .models-white { color: #ffffff; font-weight: 900; font-size: 30px; }
    .status-container { display: flex; justify-content: space-between; gap: 20px; margin-bottom: 25px; }
    .status-card { background: #161b2c; border: 1px solid #232d45; border-radius: 12px; padding: 15px; flex: 1; text-align: center; }
    .status-label { color: #8a8d9b; font-size: 11px; text-transform: uppercase; font-weight: bold; margin-bottom: 5px; }
    .status-value { font-size: 17px; font-weight: bold; }
    .status-on { color: #3fb950; }
    .status-off { color: #f85149; }
    div.stButton > button { background: linear-gradient(90deg, #007BFF 0%, #0056b3 100%); color: white !important; border-radius: 8px; font-weight: bold; width: 100%; border: none; padding: 12px; }
    .stTabs [aria-selected="true"] { color: #007BFF !important; border-bottom: 3px solid #007BFF !important; }
    </style>
    """, unsafe_allow_html=True)

# --- ЛОГИКА ТЕЛЕГРАМ ---
async def start_telegram_conn(api_id, api_hash, phone):
    client = TelegramClient(StringSession(), api_id, api_hash)
    await client.connect()
    sent_code = await client.send_code_request(phone)
    return client, sent_code.phone_code_hash

async def run_live_parser(session_str, target, days, method, placeholder):
    client = TelegramClient(StringSession(session_str), API_ID_DEFAULT, API_HASH_DEFAULT)
    await client.connect()
    results, seen = [], set()
    async def process(u):
        if not u or u.id in seen or getattr(u, 'bot', False): return
        seen.add(u.id)
        un = u.username or ""
        results.append({"ИМЯ": f"{u.first_name or ''} {u.last_name or ''}".strip(), "ЮЗЕРНЕЙМ": f"@{un}" if un else "---", "СВЯЗЬ": f"tg://resolve?domain={un}" if un else f"tg://user?id={u.id}"})
        placeholder.dataframe(pd.DataFrame(results), column_config={"СВЯЗЬ": st.column_config.LinkColumn("ЧАТ 🔵")}, use_container_width=True, hide_index=True)
    try:
        if "Все" in method:
            for char in "abcdefghijklmnopqrstuvwxyz0123456789":
                res = await client(functions.channels.GetParticipantsRequest(channel=target, filter=types.ChannelParticipantsSearch(char), offset=0, limit=1000, hash=0))
                for u in res.users: await process(u)
        else:
            limit_date = datetime.now(timezone.utc) - timedelta(days=days)
            async for m in client.iter_messages(target, limit=2000):
                if m.date < limit_date: break
                if m.sender_id: await process(await m.get_sender())
    finally: await client.disconnect()
    return results

# --- ЭКРАН ВХОДА ---
if not st.session_state.auth:
    st.markdown('<div style="text-align:center; padding-top:100px;"><span class="vm-blue">VM</span><span class="models-white"> MODELS</span></div>', unsafe_allow_html=True)
    c1, c2, c3 = st.columns([1, 1.2, 1])
    with c2:
        l_in = st.text_input("Логин")
        p_in = st.text_input("Пароль", type="password")
        if st.button("ENTER"):
            found = next((x for x in st.session_state.db["users"] if x["login"] == l_in and x["pass"] == p_in), None)
            if found:
                st.session_state.auth = True; st.session_state.user = found; st.rerun()
            else: st.error("Ошибка входа")
else:
    u = st.session_state.user
    # Хедер со статусом
    tg_name = u.get("tg_name", "")
    tg_status = f'<span class="status-on">ПОДКЛЮЧЕН <br><small>{tg_name}</small></span>' if u.get("session") else '<span class="status-off">НЕ ПОДКЛЮЧЕН</span>'
    
    st.markdown(f"""
    <div class="status-container">
        <div class="status-card"><div class="status-label">Аккаунт</div><div class="status-value">{u['login']}</div></div>
        <div class="status-card"><div class="status-label">Telegram Status</div><div class="status-value">{tg_status}</div></div>
        <div class="status-card"><div class="status-label">Лимит (24ч)</div><div class="status-value">{u.get('limit', 0)} / 50</div></div>
    </div>
    """, unsafe_allow_html=True)

    tabs = st.tabs(["⚡ СБОР", "📱 АККАУНТ", "📜 ИСТОРИЯ", "👥 КОМАНДА", "❓ ПОМОЩЬ"])

    with tabs[0]: # СБОР
        if not u.get("session"):
            st.warning("⚠️ Подключите Telegram во вкладке АККАУНТ")
        else:
            st.markdown('<div style="background:#161b2c; padding:20px; border-radius:10px; border:1px solid #232d45;">', unsafe_allow_html=True)
            target = st.text_input("Ссылка на группу (напр. nakordoni_poland)")
            method = st.radio("Алгоритм:", ["Все участники (Deep)", "Активные за период"], horizontal=True)
            days_v = 0
            if "Активные" in method:
                per = st.selectbox("Период:", ["3 дня", "7 дней", "Месяц", "3 месяца"])
                days_v = {"3 дня": 3, "7 дней": 7, "Месяц": 30, "3 месяца": 90}[per]
            
            if st.button("🚀 ЗАПУСТИТЬ ПРОЦЕСС"):
                if target:
                    if u.get('limit', 0) >= 50: st.error("Лимит исчерпан!")
                    else:
                        ph = st.empty()
                        loop = asyncio.new_event_loop(); asyncio.set_event_loop(loop)
                        data = loop.run_until_complete(run_live_parser(u["session"], target, days_v, method, ph))
                        if data:
                            for user_db in st.session_state.db["users"]:
                                if user_db["login"] == u["login"]: user_db["limit"] += 1
                            st.session_state.db["history"].append({"user": u["login"], "target": target, "count": len(data), "date": datetime.now().strftime("%d.%m %H:%M")})
                            save_db(st.session_state.db); st.success("Готово!"); st.rerun()
                else: st.warning("Укажите цель!")
            st.markdown('</div>', unsafe_allow_html=True)

    with tabs[1]: # АККАУНТ
        if u["role"] == "Админ":
            st.success(f"✅ Вы авторизованы как Администратор. Ваш ТГ: {u.get('tg_name')}")
        elif u.get("session"):
            st.success(f"✅ Ваш Telegram {u.get('tg_name')} подключен.")
            if st.button("Отвязать аккаунт"):
                for user_db in st.session_state.db["users"]:
                    if user_db["login"] == u["login"]: user_db["session"] = ""; user_db["tg_name"] = ""
                save_db(st.session_state.db); st.rerun()
        else:
            st.info("Авторизуйте свой рабочий ТГ.")
            phone = st.text_input("Номер телефона (+...)")
            if st.button("Прислать код"):
                loop = asyncio.new_event_loop(); asyncio.set_event_loop(loop)
                client, c_hash = loop.run_until_complete(start_telegram_conn(API_ID_DEFAULT, API_HASH_DEFAULT, phone))
                st.session_state.temp_client = client; st.session_state.temp_hash = c_hash; st.info("Код в Telegram!")
            
            t_code = st.text_input("Код из ТГ")
            if st.button("Активировать"):
                async def finish_auth():
                    await st.session_state.temp_client.sign_in(phone, t_code, phone_code_hash=st.session_state.temp_hash)
                    me = await st.session_state.temp_client.get_me()
                    s_str = st.session_state.temp_client.session.save()
                    tg_uname = f"@{me.username}" if me.username else f"{me.first_name}"
                    for user_db in st.session_state.db["users"]:
                        if user_db["login"] == u["login"]:
                            user_db["session"] = s_str; user_db["tg_name"] = tg_uname
                    save_db(st.session_state.db)
                loop = asyncio.new_event_loop(); asyncio.set_event_loop(loop)
                loop.run_until_complete(finish_auth()); st.rerun()

    with tabs[2]: # ИСТОРИЯ
        st.subheader("Ваши последние сборы")
        my_h = [h for h in st.session_state.db["history"] if h["user"] == u["login"]]
        if my_h: st.table(pd.DataFrame(my_h)[::-1])
        else: st.write("История пуста.")

    with tabs[3]: # КОМАНДА
        if u["role"] == "Админ":
            col1, col2 = st.columns(2)
            with col1:
                st.subheader("Новый скаут")
                nl, np = st.text_input("Username"), st.text_input("Password")
                if st.button("Создать доступ"):
                    st.session_state.db["users"].append({"login": nl, "pass": np, "role": "Работник", "session": "", "tg_name": "", "limit": 0})
                    save_db(st.session_state.db); st.success("Добавлен!"); st.rerun()
            with col2:
                st.subheader("Мониторинг")
                for i, worker in enumerate(st.session_state.db["users"]):
                    if worker["role"] != "Админ":
                        with st.expander(f"👤 {worker['login']} | ТГ: {worker.get('tg_name', '❌')}"):
                            w_h = [h for h in st.session_state.db["history"] if h["user"] == worker["login"]]
                            if w_h: st.table(pd.DataFrame(w_h))
                            if st.button("Удалить доступ", key=f"del_{i}"):
                                st.session_state.db["users"].pop(i); save_db(st.session_state.db); st.rerun()
        else: st.info("Только для администратора.")

    with tabs[4]: # ПОМОЩЬ
        st.markdown("### ❓ Как это работает\n1. Подключи ТГ во вкладке АККАУНТ\n2. Начни парсинг в СБОР\n3. Наслаждайся результатом!")

    with st.sidebar:
        if st.button("Выйти"): st.session_state.auth = False; st.rerun()
