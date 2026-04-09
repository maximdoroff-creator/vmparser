import streamlit as st
import asyncio
import pandas as pd
import os
from telethon import TelegramClient, functions, types
from datetime import datetime, timedelta, timezone

# --- КОНФИГУРАЦИЯ ---
api_id = 34321415 
api_hash = 'a858399e90e04f5992a97096b614f31e'
AVATAR_DIR = "avatars"
if not os.path.exists(AVATAR_DIR):
    os.makedirs(AVATAR_DIR)

st.set_page_config(page_title="TG Scout Pro 2.5", layout="wide")

if 'users_db' not in st.session_state:
    st.session_state.users_db = [
        {"login": "Admin.Maksym", "pass": "Maksym777", "role": "Админ"},
        {"login": "Worker1", "pass": "123", "role": "Работник"}
    ]

if 'auth' not in st.session_state:
    st.session_state.auth = False
    st.session_state.user_data = None

# --- ЛОГИКА ПАРСЕРА ---
async def run_parser(target, days, limit, method):
    client = TelegramClient('final_session', api_id, api_hash)
    await client.start()
    results = []
    seen_ids = set()

    async def process_user(u):
        if not u or u.id in seen_ids or getattr(u, 'bot', False):
            return
        seen_ids.add(u.id)
        
        avatar_path = "https://flaticon.com"
        if u.photo:
            photo_name = f"{u.id}.jpg"
            local_path = os.path.join(AVATAR_DIR, photo_name)
            if not os.path.exists(local_path):
                try:
                    await client.download_profile_photo(u, file=local_path)
                    avatar_path = local_path
                except: pass
            else:
                avatar_path = local_path
        
        un = u.username if u.username else ""
        tg_link = f"tg://resolve?domain={un}" if un else f"tg://user?id={u.id}"
        
        results.append({
            "Фото": avatar_path,
            "Имя": f"{u.first_name or ''} {u.last_name or ''}".strip() or "Скрыт",
            "Username": f"@{un}" if un else "---",
            "Ссылка": tg_link
        })

    try:
        if "Все" in method:
            alphabet = "abcdefghijklmnopqrstuvwxyz0123456789"
            p_bar = st.progress(0)
            status = st.empty()
            for i, char in enumerate(alphabet):
                status.text(f"Поиск по символу: {char} (Найдено: {len(results)})")
                p_bar.progress((i + 1) / len(alphabet))
                try:
                    participants = await client(functions.channels.GetParticipantsRequest(
                        channel=target,
                        filter=types.ChannelParticipantsSearch(char),
                        offset=0, limit=1000, hash=0
                    ))
                    for u in participants.users:
                        await process_user(u)
                except: continue
            status.empty()
            p_bar.empty()
        else:
            limit_date = datetime.now(timezone.utc) - timedelta(days=days)
            async for m in client.iter_messages(target, limit=limit):
                if m.date < limit_date: break
                if m.sender_id:
                    s = await m.get_sender()
                    await process_user(s)
    finally:
        await client.disconnect()
    return results

# --- ИНТЕРФЕЙС ---
if not st.session_state.auth:
    st.title("Вход в систему")
    l = st.text_input("ЛОГИН")
    p = st.text_input("ПАРОЛЬ", type="password")
    if st.button("ВОЙТИ"):
        user = next((u for u in st.session_state.users_db if u["login"] == l and u["pass"] == p), None)
        if user:
            st.session_state.auth = True
            st.session_state.user_data = user
            st.rerun()
        else:
            st.error("Ошибка доступа")
else:
    # Уникальные вкладки
    t_list = ["ИНСТРУКЦИЯ", "⚡️ СБОР", "📂 ИСТОРИЯ"]
    if st.session_state.user_data["role"] == "Админ":
        t_list.append("👥 КОМАНДА")
    
    tabs = st.tabs(t_list)

    with tabs[1]: # СБОР
        st.subheader("Настройки поиска")
        col1, col2 = st.columns(2)
        with col1:
            method = st.radio("Тип сбора:", ["Все участники (Максимум)", "Активные по периоду"], key="method_radio")
            target = st.text_input("Ссылка на группу (например: poehalisnami_de)", key="target_input")
        with col2:
            if "Активные" in method:
                period = st.selectbox("Выберите период:", ["3 дня", "Неделя", "Месяц", "3 месяца"], key="period_select")
                p_map = {"3 дня": 3, "Неделя": 7, "Месяц": 30, "3 месяца": 90}
                days_val = p_map[period]
                limit_msg = st.number_input("Лимит сообщений", 100, 20000, 2000, key="limit_input")
            else:
                days_val, limit_msg = 0, 0
        
        if st.button("🚀 ЗАПУСТИТЬ", key="start_btn"):
            if not target:
                st.warning("Введите ссылку!")
            else:
                with st.spinner('Парсинг запущен...'):
                    loop = asyncio.new_event_loop()
                    asyncio.set_event_loop(loop)
                    data = loop.run_until_complete(run_parser(target, days_val, limit_msg, method))
                    
                    if data:
                        df = pd.DataFrame(data)
                        st.success(f"Найдено: {len(df)}")
                        st.dataframe(
                            df, 
                            column_config={
                                "Фото": st.column_config.ImageColumn("Аватар"),
                                "Ссылка": st.column_config.LinkColumn("Открыть в TG")
                            },
                            use_container_width=True
                        )
                        st.download_button("📥 Скачать CSV", df.to_csv(index=False).encode('utf-8'), "data.csv", key="download_csv")
                    else:
                        st.warning("Ничего не найдено.")

    if st.session_state.user_data["role"] == "Админ":
        with tabs[-1]: # КОМАНДА
            cl, cr = st.columns(2)
            with cl:
                st.subheader("+ Добавить")
                nl = st.text_input("НОВЫЙ ЛОГИН")
                np = st.text_input("НОВЫЙ ПАРОЛЬ")
                nr = st.selectbox("РОЛЬ", ["Работник", "Админ"], key="role_select")
                if st.button("Создать", key="create_user_btn"):
                    st.session_state.users_db.append({"login": nl, "pass": np, "role": nr})
                    st.success("Готово!")
                    st.rerun()
            with cr:
                st.subheader("Список команды")
                for u in st.session_state.users_db:
                    st.write(f"👤 **{u['login']}** ({u['role']})")

    with st.sidebar:
        st.write(f"Вы: **{st.session_state.user_data['login']}**")
        if st.button("Выйти", key="logout_sidebar"):
            st.session_state.auth = False
            st.rerun()
