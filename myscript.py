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

st.set_page_config(page_title="VM Models | Pro System", layout="wide")

# --- ЛОГИКА БАЗЫ ДАННЫХ ---
def load_db():
    if not os.path.exists(DB_FILE):
        return {
            "users": [{"login": "Admin.Maksym", "pass": "Maksym777", "role": "Админ", "session": "", "api_id": "", "api_hash": ""}],
            "history": []
        }
    try:
        with open(DB_FILE, "r", encoding="utf-8") as f: return json.load(f)
    except: return {"users": [{"login": "Admin.Maksym", "pass": "Maksym777", "role": "Админ", "session": "", "api_id": "", "api_hash": ""}], "history": []}

def save_db(db):
    with open(DB_FILE, "w", encoding="utf-8") as f: json.dump(db, f, indent=4, ensure_ascii=False)

# Инициализация
if 'db' not in st.session_state: st.session_state.db = load_db()
if 'auth' not in st.session_state: st.session_state.auth = False
if 'user' not in st.session_state: st.session_state.user = None

# --- СТИЛЬ (VM MODELS PREMIUM) ---
st.markdown("""
    <style>
    .stApp { background-color: #0d111b; color: #ffffff; }
    .header-box { display: flex; justify-content: space-between; align-items: center; padding: 20px 0; border-bottom: 1px solid #232d45; margin-bottom: 30px; }
    .vm-blue { color: #007BFF; font-weight: 900; font-size: 32px; font-family: 'Arial Black'; }
    .models-white { color: #ffffff; font-weight: 900; font-size: 32px; }
    
    /* Читаемость текста */
    label, p, .stMarkdown, .stSubheader { color: #ffffff !important; font-weight: 600 !important; }
    
    /* Карточки и поля */
    .card { background: #161b2c; border: 1px solid #232d45; border-radius: 12px; padding: 25px; margin-bottom: 20px; }
    .stTextInput input { background-color: #0d111b !important; border: 1px solid #30363d !important; color: white !important; }
    
    /* Кнопки */
    div.stButton > button { background: linear-gradient(90deg, #007BFF 0%, #0056b3 100%); color: white !important; border: none; border-radius: 8px; font-weight: bold; width: 100%; padding: 12px; }
    .stTabs [aria-selected="true"] { color: #007BFF !important; border-bottom: 3px solid #007BFF !important; }
    </style>
    """, unsafe_allow_html=True)

# --- ЛОГИКА ТЕЛЕГРАМ ---
async def start_telegram(api_id, api_hash, phone):
    client = TelegramClient(StringSession(), api_id, api_hash)
    await client.connect()
    sent_code = await client.send_code_request(phone)
    return client, sent_code.phone_code_hash

async def run_live_parser(session_str, api_id, api_hash, target, days, method, placeholder):
    client = TelegramClient(StringSession(session_str), api_id, api_hash)
    await client.connect()
    results, seen = [], set()
    async def process(u):
        if not u or u.id in seen or getattr(u, 'bot', False): return
        seen.add(u.id)
        un = u.username or ""
        results.append({"Имя": f"{u.first_name or ''} {u.last_name or ''}".strip(), "Юзернейм": f"@{un}" if un else "---", "Чат": f"tg://resolve?domain={un}" if un else f"tg://user?id={u.id}"})
        placeholder.dataframe(pd.DataFrame(results), column_config={"Чат": st.column_config.LinkColumn("Написать")}, use_container_width=True, hide_index=True)
    
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

# --- ИНТЕРФЕЙС ---
if not st.session_state.auth:
    st.markdown('<div style="text-align:center; padding-top:100px;"><span class="vm-blue">VM</span><span class="models-white"> MODELS</span></div>', unsafe_allow_html=True)
    c1, c2, c3 = st.columns([1, 1.2, 1])
    with c2:
        l_in = st.text_input("Username")
        p_in = st.text_input("Password", type="password")
        if st.button("LOGIN"):
            found = next((x for x in st.session_state.db["users"] if x["login"] == l_in and x["pass"] == p_in), None)
            if found:
                st.session_state.auth = True; st.session_state.user = found; st.rerun()
            else: st.error("Ошибка входа")
else:
    u = st.session_state.user
    st.markdown(f'<div class="header-box"><div class="brand"><span class="vm-blue">VM</span> <span class="models-white">Models</span></div><div style="color:#8a8d9b;">{u["role"]}: {u["login"]} | <a href="/" style="color:#ff4b4b; text-decoration:none;">Выход</a></div></div>', unsafe_allow_html=True)

    tabs = st.tabs(["⚡ СБОР", "📱 АККАУНТ", "📜 ИСТОРИЯ", "👥 КОМАНДА"])

    with tabs[0]: # СБОР
        if not u.get("session"):
            st.warning("⚠️ Перейдите во вкладку 'АККАУНТ' и подключите свой Telegram.")
        else:
            st.markdown('<div class="card">', unsafe_allow_html=True)
            col_t, col_m = st.columns([2, 1])
            with col_t: target = st.text_input("Группа (Username или ссылка)")
            with col_m: method = st.selectbox("Метод сбора:", ["Активные за период", "Все участники (Глубокий)"])
            
            days_val = 0
            if "Активные" in method:
                period = st.select_slider("Период активности:", options=["3 дня", "7 дней", "Месяц", "3 месяца"])
                p_map = {"3 дня": 3, "7 дней": 7, "Месяц": 30, "3 месяца": 90}
                days_val = p_map[period]
            
            if st.button("🚀 ЗАПУСТИТЬ ПРОЦЕСС"):
                if target:
                    placeholder = st.empty()
                    loop = asyncio.new_event_loop(); asyncio.set_event_loop(loop)
                    data = loop.run_until_complete(run_live_parser(u["session"], u["api_id"], u["api_hash"], target, days_val, method, placeholder))
                    if data:
                        entry = {"user": u["login"], "target": target, "count": len(data), "date": datetime.now().strftime("%d.%m %H:%M")}
                        st.session_state.db["history"].append(entry); save_db(st.session_state.db)
                        st.success(f"Готово! Собрано: {len(data)}")
                else: st.error("Введите ссылку на группу")
            st.markdown('</div>', unsafe_allow_html=True)

    with tabs[1]: # АККАУНТ
        st.subheader("Ваш рабочий Telegram")
        if u.get("session"):
            st.success("✅ Аккаунт подключен. Вы можете парсить.")
            if st.button("Отключить этот аккаунт"):
                for user in st.session_state.db["users"]:
                    if user["login"] == u["login"]: user["session"] = ""; user["api_id"] = ""; user["api_hash"] = ""
                st.session_state.user["session"] = ""; save_db(st.session_state.db); st.rerun()
        else:
            c_a, c_b = st.columns(2)
            with c_a:
                a_id = st.number_input("API ID", value=API_ID_DEFAULT)
                a_hash = st.text_input("API HASH", value=API_HASH_DEFAULT)
                phone = st.text_input("Номер телефона")
                if st.button("Прислать код"):
                    loop = asyncio.new_event_loop(); asyncio.set_event_loop(loop)
                    client, c_hash = loop.run_until_complete(start_telegram(a_id, a_hash, phone))
                    st.session_state.temp_client = client; st.session_state.temp_hash = c_hash
                    st.session_state.temp_api = {"id": a_id, "hash": a_hash}
                    st.info("Код отправлен в ваш Telegram")
            with c_b:
                code = st.text_input("Код подтверждения")
                if st.button("Авторизовать"):
                    loop = asyncio.new_event_loop(); asyncio.set_event_loop(loop)
                    loop.run_until_complete(st.session_state.temp_client.sign_in(phone, code, phone_code_hash=st.session_state.temp_hash))
                    s_str = st.session_state.temp_client.session.save()
                    for user in st.session_state.db["users"]:
                        if user["login"] == u["login"]:
                            user["session"] = s_str; user["api_id"] = st.session_state.temp_api["id"]; user["api_hash"] = st.session_state.temp_api["hash"]
                    st.session_state.user = next(x for x in st.session_state.db["users"] if x["login"] == u["login"])
                    save_db(st.session_state.db); st.success("Успешно!"); st.rerun()

    with tabs[2]: # ИСТОРИЯ
        st.subheader("Ваша история")
        hist = [h for h in st.session_state.db["history"] if h["user"] == u["login"]]
        if hist: st.table(pd.DataFrame(hist)[::-1])
        else: st.write("Вы еще не запускали сбор.")

    with tabs[3]: # КОМАНДА
        if u["role"] == "Админ":
            col_1, col_2 = st.columns(2)
            with col_1:
                st.subheader("Новый скаут")
                nl = st.text_input("Username")
                np = st.text_input("Password")
                if st.button("Создать доступ"):
                    st.session_state.db["users"].append({"login": nl, "pass": np, "role": "Работник", "session": "", "api_id": "", "api_hash": ""})
                    save_db(st.session_state.db); st.success("Добавлен!"); st.rerun()
            with col_2:
                st.subheader("Мониторинг")
                for i, worker in enumerate(st.session_state.db["users"]):
                    if worker["role"] != "Админ":
                        with st.expander(f"👤 {worker['login']}"):
                            w_hist = [h for h in st.session_state.db["history"] if h["user"] == worker["login"]]
                            if w_hist: st.table(pd.DataFrame(w_hist))
                            else: st.write("Работник еще не начинал.")
                            if st.button("Удалить сотрудника", key=f"d_{i}"):
                                st.session_state.db["users"].pop(i); save_db(st.session_state.db); st.rerun()
        else: st.info("Только администратор видит этот раздел.")
