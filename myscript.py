import streamlit as st
import asyncio
import pandas as pd
import os
from telethon import TelegramClient, functions
from datetime import datetime, timedelta, timezone

# --- КОНФИГУРАЦИЯ ---
api_id = 34321415 
api_hash = 'a858399e90e04f5992a97096b614f31e'
AVATAR_DIR = "avatars"
if not os.path.exists(AVATAR_DIR):
    os.makedirs(AVATAR_DIR)

st.set_page_config(page_title="TG Scout Pro 2.5", layout="wide")

# Инициализация базы пользователей
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
        if u.id in seen_ids or getattr(u, 'bot', False):
            return
        seen_ids.add(u.id)
        
        # Логика аватарок
        avatar_path = None
        if u.photo:
            photo_name = f"{u.id}.jpg"
            avatar_path = os.path.join(AVATAR_DIR, photo_name)
            if not os.path.exists(avatar_path):
                await client.download_profile_photo(u, file=avatar_path)
        
        username = u.username if u.username else ""
        # Ссылка для открытия сразу в приложении
        tg_link = f"tg://resolve?domain={username}" if username else f"tg://user?id={u.id}"
        
        results.append({
            "Фото": avatar_path if avatar_path else "https://flaticon.com",
            "Имя": f"{u.first_name or ''} {u.last_name or ''}".strip() or "Скрыт",
            "Username": f"@{username}" if username else "---",
            "Ссылка": tg_link
        })

    if "Все" in method:
        # Метод глубокого парсинга через поиск по буквам (для обхода лимитов)
        alphabet = "abcdefghijklmnopqrstuvwxyz0123456789"
        progress_text = st.empty()
        for char in alphabet:
            progress_text.text(f"Парсинг по букве: {char} (Найдено: {len(results)})")
            participants = await client(functions.channels.GetParticipantsRequest(
                channel=target,
                filter=functions.channel_participants.ChannelParticipantsSearch(char),
                offset=0,
                limit=1000,
                hash=0
            ))
            for u in participants.users:
                await process_user(u)
        progress_text.empty()
    else:
        # Метод активных (по сообщениям)
        limit_date = datetime.now(timezone.utc) - timedelta(days=days)
        async for m in client.iter_messages(target, limit=limit):
            if m.date < limit_date: break
            if m.sender_id:
                s = await m.get_sender()
                if s: await process_user(s)
    
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
    t_list = ["ИНСТРУКЦИЯ", "⚡️ СБОР", "📂 ИСТОРИЯ"]
    if st.session_state.user_data["role"] == "Админ":
        t_list.append("👥 КОМАНДА")
    
    tabs = st.tabs(t_list)

    with tabs[1]:
        st.subheader("Настройки парсинга")
        col1, col2 = st.columns(2)
        with col1:
            method = st.radio("Метод:", ["Все участники (Глубокий поиск)", "Активные за период"], horizontal=True)
            target = st.text_input("Ссылка на группу (например, poehalisnami_de)")
        with col2:
            days = st.slider("Дней активности", 1, 30, 5) if "Активные" in method else 0
            limit_msg = st.number_input("Лимит проверки сообщений", 100, 10000, 1000) if "Активные" in method else 0
        
        if st.button("🚀 ЗАПУСТИТЬ ПРОЦЕСС"):
            if not target:
                st.warning("Введите ссылку на группу!")
            else:
                with st.spinner('Собираем данные...'):
                    loop = asyncio.new_event_loop()
                    asyncio.set_event_loop(loop)
                    data = loop.run_until_complete(run_parser(target, days, limit_msg, method))
                    
                    if data:
                        df = pd.DataFrame(data)
                        st.success(f"Готово! Собрано контактов: {len(df)}")
                        # Настройка отображения фото и рабочих ссылок
                        st.dataframe(
                            df, 
                            column_config={
                                "Фото": st.column_config.ImageColumn("Аватар", width="small"),
                                "Ссылка": st.column_config.LinkColumn("Открыть в TG")
                            },
                            use_container_width=True
                        )
                        # Кнопка скачивания
                        csv = df.to_csv(index=False).encode('utf-8')
                        st.download_button("📥 Скачать CSV", csv, "export.csv", "text/csv")
                    else:
                        st.warning("Участники не найдены. Проверьте доступ к группе.")

    # Вкладка КОМАНДА (без изменений)
    if st.session_state.user_data["role"] == "Админ":
        with tabs[-1]:
            cl, cr = st.columns([1, 2])
            with cl:
                st.subheader("+ Добавить")
                nl, np = st.text_input("ЛОГИН "), st.text_input("ПАРОЛЬ ")
                nr = st.selectbox("РОЛЬ", ["Работник", "Админ"])
                if st.button("Создать"):
                    st.session_state.users_db.append({"login": nl, "pass": np, "role": nr})
                    st.success("Добавлен!")
                    st.rerun()
            with cr:
                st.subheader("Структура команды")
                for u in st.session_state.users_db:
                    st.write(f"👤 **{u['login']}** ({u['role']})")

    with st.sidebar:
        st.write(f"Вы: **{st.session_state.user_data['login']}**")
        if st.button("Выйти"):
            st.session_state.auth = False
            st.rerun()
