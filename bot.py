import logging
import random
from telegram import Update, InlineKeyboardMarkup, InlineKeyboardButton
from telegram.ext import ApplicationBuilder, CommandHandler, CallbackContext, ContextTypes

TOKEN = "7513921579:AAGjJ7ChOfQBYj93WGB-SjruELN1tDolnvI"  # <-- 替换成你的 BotFather Token
logging.basicConfig(level=logging.INFO)

# 游戏状态
GAMES = {}

def get_cards():
    deck = ["A", "2", "3", "4", "5", "6", "7", "8", "9", "10", "J", "Q", "K"] * 4
    random.shuffle(deck)
    return deck

def calculate_score(cards):
    score = 0
    aces = 0
    for card in cards:
        if card in ["J", "Q", "K"]:
            score += 10
        elif card == "A":
            aces += 1
            score += 11
        else:
            score += int(card)
    while score > 21 and aces:
        score -= 10
        aces -= 1
    return score

async def join(update: Update, context: CallbackContext):
    chat_id = update.effective_chat.id
    user = update.effective_user
    if chat_id not in GAMES:
        GAMES[chat_id] = {"players": {}, "deck": get_cards(), "started": False}
    if GAMES[chat_id]["started"]:
        await update.message.reply_text("游戏已开始，无法加入！")
        return
    GAMES[chat_id]["players"][user.id] = {"name": user.first_name, "cards": []}
    await update.message.reply_text(f"{user.first_name} 加入了游戏！")

async def start(update: Update, context: CallbackContext):
    chat_id = update.effective_chat.id
    game = GAMES.get(chat_id)
    if not game or len(game["players"]) < 1:
        await update.message.reply_text("至少需要一名玩家！")
        return
    game["deck"] = get_cards()
    game["started"] = True
    for player_id in game["players"]:
        game["players"][player_id]["cards"] = [game["deck"].pop(), game["deck"].pop()]
    reply = "\n".join([f"{p['name']}：{p['cards']}（{calculate_score(p['cards'])}分）" for p in game["players"].values()])
    await update.message.reply_text(f"游戏开始！\n{reply}\n使用 /hit 抽牌，/stand 停牌")

async def hit(update: Update, context: CallbackContext):
    chat_id = update.effective_chat.id
    user = update.effective_user
    game = GAMES.get(chat_id)
    if not game or not game["started"]:
        await update.message.reply_text("游戏未开始！")
        return
    if user.id not in game["players"]:
        await update.message.reply_text("你还没加入游戏！")
        return
    player = game["players"][user.id]
    player["cards"].append(game["deck"].pop())
    score = calculate_score(player["cards"])
    if score > 21:
        await update.message.reply_text(f"{player['name']} 抽牌后爆了！{player['cards']} 总分 {score}")
    else:
        await update.message.reply_text(f"{player['name']} 抽到 {player['cards'][-1]}，当前牌组：{player['cards']} 总分 {score}")

async def stand(update: Update, context: CallbackContext):
    chat_id = update.effective_chat.id
    user = update.effective_user
    if chat_id not in GAMES:
        await update.message.reply_text("没有游戏在进行。")
        return
    await update.message.reply_text(f"{user.first_name} 停牌。等待其他玩家...（此版本未自动判断胜负）")

async def reset(update: Update, context: CallbackContext):
    chat_id = update.effective_chat.id
    if chat_id in GAMES:
        del GAMES[chat_id]
    await update.message.reply_text("游戏已重置。可重新 /join")

if __name__ == '__main__':
    app = ApplicationBuilder().token(TOKEN).build()

    app.add_handler(CommandHandler("join", join))
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("hit", hit))
    app.add_handler(CommandHandler("stand", stand))
    app.add_handler(CommandHandler("reset", reset))

    app.run_polling()
