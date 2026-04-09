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
ADMIN_SESSION = '1ApWapzMBu6a2yrYGwEl4SmIajfYwWFcdt93DPZJADeUU4mA61FcGqC9v_PqjQZm0zMQC3OZFXKLQzM_3_D15YlGyk4Z4s64oPq_dF2FXIW67-dTreso3mfFl2v3BILmO_PKoR_iBMZ5aYCUM_DY9rJcWA2_xhQ1RSmUc1HxzD9L1aDF7fiHAWcLiduwJFSOYDSuWTINIXPIIMsmqtxGxeNFM2sbgWJIFkBhGe0I4g_YaSlcV342H53kS0JUJrS2IGaTI6KgqQ6XymA9MdtjjjHRWiqb4xLRTBqyXgDvAFnnsnbegH8nMEkwudAyEa-Y-O5oCP4WJfS220InB3tNJFe8u9_qXbJw='

st.set_page_config(page_title="VM Models | Pro Dashboard", layout="wide")

# --- БАЗА ДАННЫХ ---
def load_db():
    if not os.path.exists(DB_FILE):
        return {
            "users": [{"login": "Admin.Maksym", "pass": "Maksym777", "role": "Админ", "session": ADMIN_SESSION, "tg_name": "@Maksym_Admin", "limit": 0}],
            "history": []
        }
    with open(DB_FILE, "r", encoding="utf-8") as f: return json.load(f)

def save_db(db):
    with open(DB_FILE, "w", encoding="utf-8") as f: json.dump(db, f, indent=4, ensure_ascii=False)

if 'db' not in st.session_state: st.session_state.db = load_db()

# --- СТИЛИЗАЦИЯ (DASHBOARD) ---
st.markdown("""
    <style>
    .stApp { background-color: #0d111b; color: #ffffff; }
    .vm-blue { color: #007BFF; font-weight: 900; font-size: 30px; font-family: 'Arial Black'; }
    .models-white { color: #ffffff; font-weight: 900; font-size: 30px; }
    
    /* Карточки статуса сверху */
    .status-container { display: flex; justify-content: space-between; gap: 20px; margin-bottom: 25px; }
    .status-card { background: #161b2c; border: 1px solid #232d45; border-radius: 10px; padding: 15px; flex: 1; text-align: center; }
    .status-label { color: #8a8d9b; font-size: 12px; text-transform: uppercase; font-weight: bold; margin-bottom: 5px; }
    .status-value { font-size: 16px; font-weight: bold; }
    
    /* Цвета статусов */
    .status-on { color: #3fb950; }
    .status-off { color: #f85149; }
    
    div.stButton > button { background: linear-gradient(90deg, #007BFF 0%, #0056b3 100%); color: white !important; border-radius: 8px; font-weight: bold; width: 100%; }
    .stTabs [aria-selected="true"] { color: #007BFF !important; border-bottom: 3px solid #007BFF !important; }
    </style>
    """, unsafe_allow_html=True)

# --- ЛОГИКА ---
async def check_tg_info(session_str):
    if not session_str: return None
    try:
        client = TelegramClient(StringSession(session_str), API_ID_DEFAULT, API_HASH_DEFAULT)
        await client.connect()
        me = await client.get_me()
        await client.disconnect()
        return f"@{me.username}" if me.username else me.first_name
    except: return None

async def run_live_parser(session_str, target, days, method, placeholder):
    client = TelegramClient(StringSession(session_str), API_ID_DEFAULT, API_HASH_DEFAULT)
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
if 'auth' not in st.session_state: st.session_state.auth = False

if not st.session_state.auth:
    st.markdown('<div style="text-align:center; padding-top:100px;"><span class="vm-blue">VM</span><span class="models-white"> MODELS</span></div>', unsafe_allow_html=True)
    c1, c2, c3 = st.columns([1, 1.2, 1])
    with c2:
        l_in = st.text_input("Логин")
        p_in = st.text_input("Пароль", type="password")
        if st.button("LOGIN"):
            found = next((x for x in st.session_state.db["users"] if x["login"] == l_in and x["pass"] == p_in), None)
            if found:
                st.session_state.auth = True; st.session_state.user = found; st.rerun()
            else: st.error("Доступ закрыт")
else:
    u = st.session_state.user
    
    # ВЕРХНЯЯ ПАНЕЛЬ СТАТУСОВ
    tg_status = f'<span class="status-on">ПОДКЛЮЧЕН ({u.get("tg_name", "Активен")})</span>' if u.get("session") else '<span class="status-off">НЕ ПОДКЛЮЧЕН</span>'
    
    st.markdown(f"""
    <div class="status-container">
        <div class="status-card"><div class="status-label">Пользователь</div><div class="status-value">{u['login']}</div></div>
        <div class="status-card"><div class="status-label">Telegram</div><div class="status-value">{tg_status}</div></div>
        <div class="status-card"><div class="status-label">Лимит на день</div><div class="status-value">{u.get('limit', 0)} / 50</div></div>
    </div>
    """, unsafe_allow_html=True)

    tabs = st.tabs(["⚡ СБОР", "📱 АККАУНТ", "📜 ИСТОРИЯ", "👥 КОМАНДА"])

    with tabs: # СБОР
        if not u.get("session"):
            st.warning("⚠️ Для начала работы подключите Telegram во вкладке АККАУНТ")
        else:
            st.markdown('<div style="background:#161b2c; padding:20px; border-radius:10px; border:1px solid #232d45;">', unsafe_allow_html=True)
            target = st.text_input("Ссылка на группу (напр. nakordoni_poland)")
            method = st.radio("Алгоритм:", ["Все участники (Максимум)", "Активные за период"], horizontal=True)
            days_v = 0
            if "Активные" in method:
                per = st.selectbox("Период активности:", ["3 дня", "7 дней", "Месяц", "3 месяца"])
                days_v = {"3 дня": 3, "7 дней": 7, "Месяц": 30, "3 месяца": 90}[per]
            
            if st.button("🚀 ЗАПУСТИТЬ ПАРСИНГ"):
                if target:
                    if u.get('limit', 0) >= 50:
                        st.error("Ваш дневной лимит (50) исчерпан!")
                    else:
                        ph = st.empty()
                        loop = asyncio.new_event_loop(); asyncio.set_event_loop(loop)
                        data = loop.run_until_complete(run_live_parser(u["session"], target, days_v, method, ph))
                        if data:
                            # Обновляем лимит и историю
                            for user_db in st.session_state.db["users"]:
                                if user_db["login"] == u["login"]: user_db["limit"] += 1
                            st.session_state.db["history"].append({"user": u["login"], "target": target, "count": len(data), "date": datetime.now().strftime("%d.%m %H:%M")})
                            save_db(st.session_state.db); st.success("Готово!"); st.rerun()
                else: st.warning("Введите цель!")

    with tabs: # АККАУНТ
        st.subheader("Подключение личного аккаунта")
        if u.get("session"):
            st.success(f"✅ Ваш Telegram {u.get('tg_name')} успешно привязан.")
            if st.button("Отвязать аккаунт"):
                for user_db in st.session_state.db["users"]:
                    if user_db["login"] == u["login"]: user_db["session"] = ""; user_db["tg_name"] = ""
                save_db(st.session_state.db); st.rerun()
        else:
            st.info("Введите данные из my.telegram.org для активации.")
            phone = st.text_input("Ваш номер телефона (+...)")
            if st.button("Получить код"):
                loop = asyncio.new_event_loop(); asyncio.set_event_loop(loop)
                client = TelegramClient(StringSession(), API_ID_DEFAULT, API_HASH_DEFAULT)
                await client.connect()
                res = await client.send_code_request(phone)
                st.session_state.temp_client = client; st.session_state.temp_hash = res.phone_code_hash; st.info("Код отправлен!")
            
            t_code = st.text_input("Код из ТГ")
            if st.button("Активировать"):
                loop = asyncio.new_event_loop(); asyncio.set_event_loop(loop)
                await st.session_state.temp_client.sign_in(phone, t_code, phone_code_hash=st.session_state.temp_hash)
                me = await st.session_state.temp_client.get_me()
                session_str = st.session_state.temp_client.session.save()
                for user_db in st.session_state.db["users"]:
                    if user_db["login"] == u["login"]:
                        user_db["session"] = session_str; user_db["tg_name"] = f"@{me.username}" if me.username else me.first_name
                save_db(st.session_state.db); st.success("Успешно подключено!"); st.rerun()

    with tabs: # КОМАНДА
        if u["role"] == "Админ":
            st.subheader("Мониторинг скаутов")
            for i, worker in enumerate(st.session_state.db["users"]):
                if worker["role"] != "Админ":
                    with st.expander(f"👤 {worker['login']} | Статус: {'✅' if worker['session'] else '❌'} | Лимит: {worker.get('limit',0)}/50"):
                        w_hist = [h for h in st.session_state.db["history"] if h["user"] == worker["login"]]
                        if w_hist: st.table(pd.DataFrame(w_hist))
                        if st.button("Закрыть доступ", key=f"del_{i}"):
                            st.session_state.db["users"].pop(i); save_db(st.session_state.db); st.rerun()

    with st.sidebar:
        if st.button("Выйти"):
            st.session_state.auth = False; st.rerun()

                            st.session_state.db["users"].pop(i); save_db(st.session_state.db); st.rerun()

