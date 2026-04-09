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

st.set_page_config(page_title="VM Models Pro", layout="wide", initial_sidebar_state="collapsed")

# --- БАЗА ДАННЫХ ---
def load_db():
    def_db = {"users": [{"login": "Admin.Maksym", "pass": "Maksym777", "role": "Админ", "session": ADMIN_SESSION, "tg_name": "@Maksym_Admin", "limit": 0}], "history": []}
    if not os.path.exists(DB_FILE): return def_db
    try:
        with open(DB_FILE, "r", encoding="utf-8") as f:
            data = json.load(f)
            for u in data.get("users", []):
                u.setdefault("limit", 0)
                u.setdefault("tg_name", "")
                u.setdefault("session", "")
            return data
    except: return def_db

def save_db(db):
    with open(DB_FILE, "w", encoding="utf-8") as f:
        json.dump(db, f, indent=4, ensure_ascii=False)

st.session_state.db = load_db()

# --- АНТИ-ВЫЛЕТ ---
if 'auth' not in st.session_state:
    u_param = st.query_params.get("u")
    if u_param:
        match = next((x for x in st.session_state.db["users"] if x["login"] == u_param), None)
        if match: st.session_state.auth, st.session_state.user = True, match
        else: st.session_state.auth = False
    else: st.session_state.auth = False

# --- СТИЛИЗАЦИЯ (ФИКС ЦВЕТОВ) ---
st.markdown("""
    <style>
    [data-testid="collapsedControl"] { display: none; }
    .stApp { background-color: #0d111b; color: #ffffff !important; }
    .brand-vm { color: #007BFF !important; font-weight: 900; font-family: 'Arial Black'; }
    .brand-models { color: #ffffff !important; font-weight: 900; }
    
    /* Яркие статусы */
    .status-on { color: #00ff00 !important; font-weight: bold; }
    .status-off { color: #ff4b4b !important; font-weight: bold; }
    
    .stat-card { background: #161b2c; border: 1px solid #232d45; border-radius: 12px; padding: 20px; text-align: center; }
    .stat-label { color: #8a8d9b; font-size: 11px; text-transform: uppercase; font-weight: bold; }

    /* ВСЕ КНОПКИ СИННИЕ */
    button, .stDownloadButton > button, .stButton > button {
        background: linear-gradient(90deg, #007BFF 0%, #0056b3 100%) !important;
        color: white !important; border: none !important; border-radius: 8px !important;
        padding: 10px 20px !important; font-weight: bold !important; width: 100% !important;
    }
    button:hover { transform: translateY(-1px); box-shadow: 0 4px 15px rgba(0,123,255,0.4); }
    
    .stTabs [aria-selected="true"] { color: #007BFF !important; border-bottom-color: #007BFF !important; }
    .stTextInput input { background-color: #1a1a1a !important; border: 1px solid #333 !important; color: white !important; }
    </style>
    """, unsafe_allow_html=True)

# --- УТИЛИТА ДЛЯ ЗАПУСКА ASYNC ---
def run_async(coro):
    try:
        loop = asyncio.get_event_loop()
    except RuntimeError:
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
    return loop.run_until_complete(coro)

# --- ЛОГИКА ТЕЛЕГРАМ ---
async def start_auth(phone):
    client = TelegramClient(StringSession(), API_ID_DEFAULT, API_HASH_DEFAULT)
    await client.connect()
    res = await client.send_code_request(phone)
    return client, res.phone_code_hash

async def run_live_parser(session_str, target, days, method, placeholder):
    client = TelegramClient(StringSession(session_str), API_ID_DEFAULT, API_HASH_DEFAULT)
    await client.connect()
    results, seen = [], set()
    async def process(u_obj):
        if not u_obj or u_obj.id in seen or getattr(u_obj, 'bot', False): return
        seen.add(u_obj.id)
        un = u_obj.username or ""
        results.append({"ИМЯ": f"{u_obj.first_name or ''} {u_obj.last_name or ''}".strip(), "ЮЗЕРНЕЙМ": f"@{un}" if un else "---", "СВЯЗЬ": f"tg://resolve?domain={un}" if un else f"tg://user?id={u_obj.id}"})
        placeholder.dataframe(pd.DataFrame(results), column_config={"СВЯЗЬ": st.column_config.LinkColumn("ЧАТ 🔵")}, use_container_width=True, hide_index=True)
    try:
        if "Все" in method:
            for char in "abcdefghijklmnopqrstuvwxyz0123456789":
                res = await client(functions.channels.GetParticipantsRequest(channel=target, filter=types.ChannelParticipantsSearch(char), offset=0, limit=1000, hash=0))
                for p in res.users: await process(p)
        else:
            limit_date = datetime.now(timezone.utc) - timedelta(days=days)
            async for m in client.iter_messages(target, limit=2000):
                if m.date < limit_date: break
                if m.sender_id: await process(await m.get_sender())
    finally: await client.disconnect()
    return results

# --- ИНТЕРФЕЙС ---
if not st.session_state.get('auth'):
    st.markdown('<div style="text-align:center; padding-top:80px; margin-bottom:30px;"><span class="brand-vm" style="font-size:50px;">VM</span> <span class="brand-models" style="font-size:50px;">Models</span></div>', unsafe_allow_html=True)
    _, col_login, _ = st.columns([1.5, 1, 1.5])
    with col_login:
        l_in = st.text_input("Username").strip()
        p_in = st.text_input("Password", type="password").strip()
        if st.button("ENTER"):
            st.session_state.db = load_db()
            user = next((x for x in st.session_state.db["users"] if x["login"] == l_in and x["pass"] == p_in), None)
            if user:
                st.session_state.auth, st.session_state.user = True, user
                st.query_params["u"] = l_in
                st.rerun()
            else: st.error("Access Denied")
else:
    u = st.session_state.user
    st.markdown(f'<div style="display:flex; justify-content:space-between; align-items:center; padding:15px; border-bottom:1px solid #232d45; margin-bottom:20px;"><div style="font-size:24px;"><span class="brand-vm">VM</span> <span class="brand-models">Models</span></div><div style="color:#8a8d9b; font-size:14px;">{u.get("role")}: <b>{u["login"]}</b></div></div>', unsafe_allow_html=True)

    # ДАШБОРД
    tg_name = u.get("tg_name", "")
    tg_html = f'<span class="status-on">ПОДКЛЮЧЕН</span><br><small style="color:#8a8d9b;">{tg_name}</small>' if u.get("session") else '<span class="status-off">НЕ ПОДКЛЮЧЕН</span>'
    
    cs1, cs2, cs3 = st.columns(3)
    cs1.markdown(f'<div class="stat-card"><div class="stat-label">Аккаунт</div><div class="stat-value">{u["login"]}</div></div>', unsafe_allow_html=True)
    cs2.markdown(f'<div class="stat-card"><div class="stat-label">Telegram Status</div><div class="stat-value">{tg_html}</div></div>', unsafe_allow_html=True)
    cs3.markdown(f'<div class="stat-card"><div class="stat-label">Лимит (24ч)</div><div class="stat-value">{u.get("limit", 0)} / 50</div></div>', unsafe_allow_html=True)

    tabs = st.tabs(["⚡ СБОР", "📱 АККАУНТ", "📜 ИСТОРИЯ", "👥 КОМАНДА", "🚪 ВЫХОД"])

    with tabs[0]: # СБОР
        sess_str = u.get("session", ADMIN_SESSION if u["role"] == "Админ" else "")
        if not sess_str: st.warning("⚠️ Подключите Telegram в АККАУНТЕ")
        else:
            st.markdown('<div style="background:#161b2c; padding:25px; border-radius:12px; border:1px solid #232d45;">', unsafe_allow_html=True)
            target = st.text_input("Группа (Username или ссылка)")
            col_m, col_p = st.columns(2)
            with col_m: method = st.radio("Метод:", ["Все участники", "Активные за период"], horizontal=True)
            with col_p:
                days_v = 0
                if "Активные" in method:
                    per = st.selectbox("Период:", ["3 дня", "7 дней", "Месяц", "3 месяца"])
                    days_v = {"3 дня": 3, "7 дней": 7, "Месяц": 30, "3 месяца": 90}[per]
            if st.button("🚀 ЗАПУСТИТЬ"):
                if target:
                    if u.get('limit', 0) >= 50: st.error("Лимит исчерпан!")
                    else:
                        ph = st.empty()
                        data = run_async(run_live_parser(sess_str, target, days_v, method, ph))
                        if data:
                            for db_u in st.session_state.db["users"]:
                                if db_u["login"] == u["login"]: 
                                    db_u["limit"] += 1; st.session_state.user["limit"] = db_u["limit"]
                            st.session_state.db["history"].append({"user": u["login"], "target": target, "count": len(data), "date": datetime.now().strftime("%d.%m %H:%M")})
                            save_db(st.session_state.db)
                            txt = "\n".join([i['ЮЗЕРНЕЙМ'] for i in data if i['ЮЗЕРНЕЙМ'] != "---"])
                            st.download_button("📥 СКАЧАТЬ В БЛОКНОТ (@)", txt, "usernames.txt")
                else: st.warning("Введите цель!")
            st.markdown('</div>', unsafe_allow_html=True)

    with tabs[1]: # АККАУНТ
        st.subheader("Подключение Telegram")
        if u["role"] == "Админ": st.success(f"✅ Админ-аккаунт активен: {u.get('tg_name')}")
        elif u.get("session"):
            st.success(f"✅ Подключено: {u.get('tg_name')}")
            if st.button("Отключить"):
                for db_u in st.session_state.db["users"]:
                    if db_u["login"] == u["login"]: db_u["session"], db_u["tg_name"] = "", ""
                save_db(st.session_state.db); st.rerun()
        else:
            phone = st.text_input("Телефон (+...)")
            if st.button("Прислать код"):
                client, hash_c = run_async(start_auth(phone))
                st.session_state.tmp_c, st.session_state.tmp_h = client, hash_c; st.info("Код отправлен!")
            code = st.text_input("Код")
            if st.button("АКТИВИРОВАТЬ"):
                async def finish():
                    await st.session_state.tmp_c.sign_in(phone, code, phone_code_hash=st.session_state.tmp_h)
                    me = await st.session_state.tmp_c.get_me()
                    s = st.session_state.tmp_c.session.save()
                    un = f"@{me.username}" if me.username else me.first_name
                    for db_u in st.session_state.db["users"]:
                        if db_u["login"] == u["login"]: db_u["session"], db_u["tg_name"] = s, un
                    save_db(st.session_state.db)
                run_async(finish()); st.rerun()

    with tabs[2]: # ИСТОРИЯ
        my_h = [h for h in st.session_state.db["history"] if h["user"] == u["login"]]
        if my_h: st.table(pd.DataFrame(my_h)[::-1])
        else: st.write("Пусто.")

    with tabs[3]: # КОМАНДА
        if u["role"] == "Админ":
            col1, col2 = st.columns(2)
            with col1:
                nl, np = st.text_input("Логин"), st.text_input("Пароль")
                if st.button("Добавить скаута"):
                    st.session_state.db["users"].append({"login": nl, "pass": np, "role": "Работник", "session": "", "tg_name": "", "limit": 0})
                    save_db(st.session_state.db); st.rerun()
            with col2:
                for i, worker in enumerate(st.session_state.db["users"]):
                    if worker["role"] != "Админ":
                        with st.expander(f"👤 {worker['login']} ({worker.get('limit',0)}/50)"):
                            if st.button("Удалить", key=f"del_{i}"):
                                st.session_state.db["users"].pop(i); save_db(st.session_state.db); st.rerun()

    with tabs[4]: # ВЫХОД
        if st.button("ПОДТВЕРДИТЬ ВЫХОД"):
            st.query_params.clear(); st.session_state.clear(); st.rerun()
