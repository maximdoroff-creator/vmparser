import streamlit as st
import asyncio
import pandas as pd
import os
import json
from telethon import TelegramClient, functions, types
from telethon.sessions import StringSession
from datetime import datetime, timedelta, timezone

# --- КОНФИГУРАЦИЯ ---
DB_FILE = "vm_database.json"
ADMIN_LOGIN = "Admin.Maksym"
ADMIN_PASS = "Maksym777"
ADMIN_SESSION = '1ApWapzMBu6a2yrYGwEl4SmIajfYwWFcdt93DPZJADeUU4mA61FcGqC9v_PqjQZm0zMQC3OZFXKLQzM_3_D15YlGyk4Z4s64oPq_dF2FXIW67-dTreso3mfFl2v3BILmO_PKoR_iBMZ5aYCUM_DY9rJcWA2_xhQ1RSmUc1HxzD9L1aDF7fiHAWcLiduwJFSOYDSuWTINIXPIIMsmqtxGxeNFM2sbgWJIFkBhGe0I4g_YaSlcV342H53kS0JUJrS2IGaTI6KgqQ6XymA9MdtjjjHRWiqb4xLRTBqyXgDvAFnnsnbegH8nMEkwudAyEa-Y-O5oCP4WJfS220InB3tNJFe8u9_qXbJw='
API_ID_DEFAULT = 34321415
API_HASH_DEFAULT = 'a858399e90e04f5992a97096b614f31e'

st.set_page_config(page_title="VM Models Pro", layout="wide", initial_sidebar_state="collapsed")

# --- БАЗА ДАННЫХ ---
def load_db():
    def_admin = {"login": ADMIN_LOGIN, "pass": ADMIN_PASS, "role": "Админ", "session": ADMIN_SESSION, "tg_name": "@Maksym_Admin", "limit": 0, "api_id": API_ID_DEFAULT, "api_hash": API_HASH_DEFAULT}
    if not os.path.exists(DB_FILE):
        return {"users": [def_admin], "history": []}
    try:
        with open(DB_FILE, "r", encoding="utf-8") as f:
            data = json.load(f)
            if not any(x["login"] == ADMIN_LOGIN for x in data["users"]):
                data["users"].append(def_admin)
            return data
    except:
        return {"users": [def_admin], "history": []}

def save_db(db):
    with open(DB_FILE, "w", encoding="utf-8") as f:
        json.dump(db, f, indent=4, ensure_ascii=False)

# Инициализация
if 'results' not in st.session_state: st.session_state.results = None

# --- ПРОВЕРКА АВТОРИЗАЦИИ ---
if 'auth' not in st.session_state:
    saved_u = st.query_params.get("u")
    db_temp = load_db()
    if saved_u:
        match = next((x for x in db_temp["users"] if x["login"] == saved_u), None)
        if match:
            st.session_state.auth = True
            st.session_state.user_login = saved_u
    else: st.session_state.auth = False

# Загружаем актуальные данные юзера
if st.session_state.get('auth'):
    db_now = load_db()
    u = next((x for x in db_now["users"] if x["login"] == st.session_state.user_login), None)
else: u = None

# --- СТИЛИЗАЦИЯ ---
st.markdown("""
    <style>
    [data-testid="collapsedControl"] { display: none; }
    .stApp { background-color: #0d111b; color: #ffffff !important; }
    .brand-vm { color: #007BFF !important; font-weight: 900; font-size: 32px; font-family: 'Arial Black'; }
    .brand-models { color: #ffffff !important; font-weight: 900; }
    .status-on { color: #00ff00 !important; font-weight: bold; }
    .status-off { color: #ff3333 !important; font-weight: bold; }
    .stat-card { background: #161b2c; border: 1px solid #232d45; border-radius: 12px; padding: 20px; text-align: center; }
    .stat-label { color: #8a8d9b; font-size: 11px; text-transform: uppercase; font-weight: bold; margin-bottom: 8px; }
    div.stButton > button, div.stDownloadButton > button {
        background-color: #1f2937 !important; color: white !important; 
        border: 1px solid #374151 !important; border-radius: 8px !important;
        padding: 10px 20px !important; font-weight: 600 !important; width: 100% !important; transition: 0.2s;
    }
    div.stButton > button:hover, div.stDownloadButton > button:hover { border-color: #007BFF !important; background-color: #111827 !important; }
    .stTabs [aria-selected="true"] { color: #007BFF !important; border-bottom-color: #007BFF !important; }
    .stTextInput input { background-color: #1a1a1a !important; border: 1px solid #333 !important; color: white !important; }
    </style>
    """, unsafe_allow_html=True)

def run_sync(coro):
    loop = asyncio.new_event_loop(); asyncio.set_event_loop(loop)
    try: return loop.run_until_complete(coro)
    finally: loop.close()

async def run_live_parser(u_data, target, days, method, placeholder):
    client = TelegramClient(StringSession(u_data['session']), int(u_data['api_id']), u_data['api_hash'])
    await client.connect()
    results, seen = [], set()
    async def process(obj):
        if not obj or obj.id in seen or getattr(obj, 'bot', False): return
        seen.add(obj.id); un = getattr(obj, 'username', "") or ""
        results.append({
            "ИМЯ": f"{getattr(obj, 'first_name', 'User') or ''} {getattr(obj, 'last_name', '') or ''}".strip(),
            "ЮЗЕРНЕЙМ": f"@{un}" if un else "---",
            "СВЯЗЬ": f"tg://resolve?domain={un}" if un else f"tg://user?id={obj.id}"
        })
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

# --- ЭКРАН ВХОДА ---
if not st.session_state.get('auth'):
    st.markdown('<div style="text-align:center; padding-top:80px; margin-bottom:30px;"><span class="brand-vm" style="font-size:50px;">VM</span> <span class="brand-models" style="font-size:50px;">Models</span></div>', unsafe_allow_html=True)
    _, col_login, _ = st.columns([1.5, 1, 1.5])
    with col_login:
        l_in = st.text_input("Username").strip()
        p_in = st.text_input("Password", type="password").strip()
        if st.button("LOGIN TO SYSTEM"):
            db = load_db()
            if l_in == ADMIN_LOGIN and p_in == ADMIN_PASS:
                st.session_state.auth, st.session_state.user_login = True, ADMIN_LOGIN
                st.query_params["u"] = ADMIN_LOGIN; st.rerun()
            user_match = next((x for x in db["users"] if x["login"] == l_in and x["pass"] == p_in), None)
            if user_match:
                st.session_state.auth, st.session_state.user_login = True, l_in
                st.query_params["u"] = l_in; st.rerun()
            else: st.error("Access Denied")
else:
    # --- ИНТЕРФЕЙС ---
    st.markdown(f'<div style="display:flex; justify-content:space-between; align-items:center; padding:15px; border-bottom:1px solid #232d45; margin-bottom:20px;"><div style="font-size:24px;"><span class="brand-vm">VM</span> <span class="brand-models">Models</span></div><div style="color:#8a8d9b; font-size:14px;">{u.get("role")}: <b>{u["login"]}</b></div></div>', unsafe_allow_html=True)

    tg_stat = f'<span class="status-on">ПОДКЛЮЧЕН</span><br><small style="color:#8a8d9b;">{u.get("tg_name")}</small>' if u.get("session") else '<span class="status-off">НЕ ПОДКЛЮЧЕН</span>'
    cs1, cs2, cs3 = st.columns(3)
    cs1.markdown(f'<div class="stat-card"><div class="stat-label">Аккаунт</div><div style="font-size:18px; font-weight:800;">{u["login"]}</div></div>', unsafe_allow_html=True)
    cs2.markdown(f'<div class="stat-card"><div class="stat-label">Telegram Status</div><div style="font-size:18px;">{tg_stat}</div></div>', unsafe_allow_html=True)
    cs3.markdown(f'<div class="stat-card"><div class="stat-label">Лимит (24ч)</div><div style="font-size:18px; font-weight:800;">{u.get("limit", 0)} / 50</div></div>', unsafe_allow_html=True)

    tabs = st.tabs(["⚡ СБОР", "📱 АККАУНТ", "📜 ИСТОРИЯ", "👥 КОМАНДА", "🚪 ВЫХОД"])

    with tabs[0]: # СБОР
        if not u.get("session"): st.warning("⚠️ Сначала подключите Telegram в АККАУНТЕ")
        else:
            st.markdown('<div style="background:#161b2c; padding:25px; border-radius:12px; border:1px solid #232d45;">', unsafe_allow_html=True)
            target = st.text_input("Ссылка на группу")
            col_m, col_p = st.columns(2)
            with col_m: method = st.radio("Метод:", ["Все участники", "Активные за период"], horizontal=True)
            with col_p:
                days_v = 0
                if "Активные" in method:
                    per = st.selectbox("Период активности:", ["3 дня", "7 дней", "Месяц", "3 месяца"])
                    days_v = {"3 дня": 3, "7 дней": 7, "Месяц": 30, "3 месяца": 90}[per]
            
            if st.button("🚀 ЗАПУСТИТЬ ПРОЦЕСС"):
                if target:
                    if u.get('limit', 0) >= 50: st.error("Лимит исчерпан!")
                    else:
                        ph = st.empty(); data = run_sync(run_live_parser(u, target, days_v, method, ph))
                        if data:
                            db = load_db()
                            for db_u in db["users"]:
                                if db_u["login"] == u["login"]: db_u["limit"] += 1
                            usernames_txt = "\n".join([i['ЮЗЕРНЕЙМ'] for i in data if i['ЮЗЕРНЕЙМ'] != "---"])
                            st.session_state.results = {"df": pd.DataFrame(data), "txt": usernames_txt}
                            db["history"].append({"user": u["login"], "target": target, "count": len(data), "date": datetime.now().strftime("%d.%m %H:%M"), "data": usernames_txt})
                            save_db(db); st.rerun()
            st.markdown('</div>', unsafe_allow_html=True)
            if st.session_state.results:
                st.write("---"); st.dataframe(st.session_state.results["df"], use_container_width=True, hide_index=True)
                st.download_button("📥 СКАЧАТЬ В БЛОКНОТ (@)", st.session_state.results["txt"], "scout_list.txt")

    with tabs[1]: # АККАУНТ
        st.subheader("Настройки Telegram")
        if u.get("session"):
            st.success(f"✅ Аккаунт {u.get('tg_name')} привязан.")
            if st.button("Отключить"):
                db = load_db()
                for d in db["users"]:
                    if d["login"] == u["login"]: d["session"], d["tg_name"] = "", ""
                save_db(db); st.rerun()
        else:
            st.markdown('Ссылка: <a href="https://my.telegram.org" target="_blank" style="color:#007BFF;">https://my.telegram.org</a>', unsafe_allow_html=True)
            aid, ahash, phone = st.text_input("API ID"), st.text_input("API HASH"), st.text_input("ТЕЛЕФОН")
            if st.button("ПОЛУЧИТЬ КОД"):
                async def get_c():
                    c = TelegramClient(StringSession(), int(aid), ahash); await c.connect()
                    res = await c.send_code_request(phone); return c.session.save(), res.phone_code_hash
                s, h = run_sync(get_c()); st.session_state.tmp_s, st.session_state.tmp_h, st.session_state.tmp_p, st.session_state.tmp_id, st.session_state.tmp_hash = s, h, phone, aid, ahash
                st.info("Код отправлен!")
            tc = st.text_input("КОД")
            if st.button("АКТИВИРОВАТЬ"):
                async def finish():
                    c = TelegramClient(StringSession(st.session_state.tmp_s), int(st.session_state.tmp_id), st.session_state.tmp_hash)
                    await c.connect(); await c.sign_in(st.session_state.tmp_p, tc, phone_code_hash=st.session_state.tmp_h)
                    me = await c.get_me(); uname = f"@{me.username}" if me.username else me.first_name
                    db = load_db()
                    for d in db["users"]:
                        if d["login"] == u["login"]: d["session"], d["tg_name"], d["api_id"], d["api_hash"] = c.session.save(), uname, st.session_state.tmp_id, st.session_state.tmp_hash
                    save_db(db)
                run_sync(finish()); st.rerun()

    with tabs[2]: # ИСТОРИЯ
        st.subheader("Ваша история")
        db_h = load_db()
        my_h = [h for h in db_h["history"] if h["user"] == u["login"]]
        if my_h:
            for i, item in enumerate(reversed(my_h)):
                c1, c2, c3, c4 = st.columns(4)
                c1.write(f"📁 {item['target']}"); c2.write(f"👥 {item['count']}"); c3.write(f"📅 {item['date']}")
                if "data" in item: c4.download_button("📥 .TXT", item['data'], f"data_{i}.txt", key=f"h_{i}")
                st.write("---")
        else: st.write("История пуста.")

    with tabs[3]: # КОМАНДА
        if u["role"] == "Админ":
            col1, col2 = st.columns(2)
            with col1:
                st.subheader("Новый скаут")
                nl, np = st.text_input("Логин"), st.text_input("Пароль")
                if st.button("Создать доступ"):
                    db = load_db()
                    db["users"].append({"login": nl, "pass": np, "role": "Работник", "session": "", "tg_name": "", "limit": 0}); save_db(db); st.rerun()
            with col2:
                db = load_db()
                for i, worker in enumerate(db["users"]):
                    if worker["role"] != "Админ":
                        with st.expander(f"👤 {worker['login']} ({worker.get('limit',0)}/50)"):
                            w_h = [h for h in db["history"] if h["user"] == worker["login"]]
                            if w_h:
                                for it in reversed(w_h): st.write(f"{it['date']} | {it['target']} | {it['count']} чел.")
                            if st.button("Удалить", key=f"del_{i}"):
                                db["users"].pop(i); save_db(db); st.rerun()
        else: st.info("Только для админа.")

    with tabs[4]: # ВЫХОД
        if st.button("ВЫЙТИ"):
            st.session_state.auth = False; st.session_state.user_login = None; st.rerun()


