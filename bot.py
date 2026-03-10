import logging
import json
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
ApplicationBuilder,
CommandHandler,
MessageHandler,
CallbackQueryHandler,
ContextTypes,
filters
)

TOKEN = "8771277043:AAF9ot5lj0G0HwGImuLHi-JUNSTKM6TEzz8"
ADMIN_ID = 5889477300
ADMIN_USERNAME = "Kroniq_Pensia"

queue = []
waiting_for_id = {}

logging.basicConfig(level=logging.INFO)

def save_log(data):
    try:
        with open("players.json","r") as f:
            players = json.load(f)
    except:
        players = []

    players.append(data)

    with open("players.json","w") as f:
        json.dump(players,f,indent=2)

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):

    keyboard = [[InlineKeyboardButton("📨 Подать заявку в клан 3TF",callback_data="apply")]]

    await update.message.reply_text(
        "Добро пожаловать в систему заявок клана 3TF",
        reply_markup=InlineKeyboardMarkup(keyboard)
    )

async def apply(update: Update, context: ContextTypes.DEFAULT_TYPE):

    query = update.callback_query
    await query.answer()

    await query.message.reply_text(
        "Отправьте:\n\n"
        "1️⃣ Скрин профиля с временем\n"
        "2️⃣ Видео 1 катки ММ"
    )

async def media(update: Update, context: ContextTypes.DEFAULT_TYPE):

    user = update.message.from_user

    if user.id not in queue:
        queue.append(user.id)

    await context.bot.forward_message(
        ADMIN_ID,
        update.message.chat_id,
        update.message.message_id
    )

    keyboard = [[
        InlineKeyboardButton("✅ Принять",callback_data=f"accept_{user.id}"),
        InlineKeyboardButton("❌ Отказать",callback_data=f"reject_{user.id}")
    ]]

    await context.bot.send_message(
        ADMIN_ID,
        f"Новая заявка\n@{user.username}\nID {user.id}\n\nВ очереди: {len(queue)}",
        reply_markup=InlineKeyboardMarkup(keyboard)
    )

async def decision(update: Update, context: ContextTypes.DEFAULT_TYPE):

    query = update.callback_query
    await query.answer()

    data = query.data

    if "accept_" in data:

        user_id = int(data.split("_")[1])

        waiting_for_id[user_id] = True

        await context.bot.send_message(
            user_id,
            "Поздравляю вы приняты в клан 3TF\n\nНапишите ваш игровой ID"
        )

        await query.edit_message_text("Игрок принят")

    if "reject_" in data:

        user_id = int(data.split("_")[1])

        keyboard=[[InlineKeyboardButton(
            "Связаться с админом",
            url=f"https://t.me/{ADMIN_USERNAME}"
        )]]

        await context.bot.send_message(
            user_id,
            "Ваша заявка отклонена",
            reply_markup=InlineKeyboardMarkup(keyboard)
        )

        await query.edit_message_text("Игрок отклонён")

async def get_id(update: Update, context: ContextTypes.DEFAULT_TYPE):

    user = update.message.from_user

    if user.id in waiting_for_id:

        player_id = update.message.text

        save_log({
            "telegram":user.id,
            "username":user.username,
            "game_id":player_id
        })

        keyboard=[[InlineKeyboardButton(
            "📨 Пригласить",
            callback_data=f"invite_{user.id}"
        )]]

        await context.bot.send_message(
            ADMIN_ID,
            f"Игрок отправил ID\n\n@{user.username}\nGameID: {player_id}",
            reply_markup=InlineKeyboardMarkup(keyboard)
        )

        await update.message.reply_text("ID отправлен админу")

        del waiting_for_id[user.id]

async def invite(update: Update, context: ContextTypes.DEFAULT_TYPE):

    query = update.callback_query
    await query.answer()

    user_id = int(query.data.split("_")[1])

    await context.bot.send_message(
        user_id,
        "Вам был отправлен запрос в клан 3TF"
    )

    await query.edit_message_text("Приглашение отправлено")

async def admin(update: Update, context: ContextTypes.DEFAULT_TYPE):

    if update.message.from_user.id != ADMIN_ID:
        return

    keyboard=[
        [InlineKeyboardButton("📋 Очередь заявок",callback_data="queue")],
        [InlineKeyboardButton("📊 Лог игроков",callback_data="logs")]
    ]

    await update.message.reply_text(
        "Панель администратора",
        reply_markup=InlineKeyboardMarkup(keyboard)
    )

async def admin_panel(update: Update, context: ContextTypes.DEFAULT_TYPE):

    query = update.callback_query
    await query.answer()

    if query.data=="queue":

        await query.message.reply_text(f"В очереди {len(queue)} игроков")

    if query.data=="logs":

        try:
            with open("players.json") as f:
                data=json.load(f)

            text="Игроки:\n"

            for p in data:
                text+=f"\n@{p['username']} | {p['game_id']}"

        except:
            text="Лог пуст"

        await query.message.reply_text(text)

def main():

    app=ApplicationBuilder().token(TOKEN).build()

    app.add_handler(CommandHandler("start",start))
    app.add_handler(CommandHandler("admin",admin))

    app.add_handler(CallbackQueryHandler(apply,pattern="apply"))
    app.add_handler(CallbackQueryHandler(decision,pattern="accept_|reject_"))
    app.add_handler(CallbackQueryHandler(invite,pattern="invite_"))
    app.add_handler(CallbackQueryHandler(admin_panel))

    app.add_handler(MessageHandler(filters.PHOTO | filters.VIDEO,media))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND,get_id))

    app.run_polling()

if __name__=="__main__":
    main()