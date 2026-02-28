import asyncio
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ApplicationBuilder, ContextTypes, CommandHandler, MessageHandler, filters, ConversationHandler, CallbackQueryHandler
import dotenv
import os
from sqlalchemy.orm import Session
from sqlalchemy import insert
from db import engine, Player, Match
from functools import partial
from enum import Enum

A1 = 0
A2 = 1
B1 = 2 
B2 = 3
SCORE = 4
END = 5

dotenv.load_dotenv()
TOKEN = os.environ.get("BOT_TOKEN")

REGISTERED_PLAYERS = ["Alice", "Bob", "Charlie", "Derek", "Pino", "Gino", "Richard", "Legolas"]

def get_player_keyboard(players:list[str]):
    keyboard = []    
    for i in range(0, len(players), 2):
        row = [InlineKeyboardButton(p, callback_data=p) for p in players[i:i+2]]
        keyboard.append(row)
    return InlineKeyboardMarkup(keyboard)

def get_teams_keyboard(data: dict):
    keyboard = []    
    teams = {"A": f"Team A\n {data['A']}", "B": f"Team B\n {data['B']}"}
     
    row = [InlineKeyboardButton(v, callback_data=k) for k,v in teams.items()]
    keyboard.append(row)
    return InlineKeyboardMarkup(keyboard)


async def start_match(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "Who is Player 1 for Team A?", 
        reply_markup=get_player_keyboard(REGISTERED_PLAYERS)
    )
    return 0


async def get_player(update:Update, context:ContextTypes.DEFAULT_TYPE, team: str, state_id: int, text: str = "", is_last_player: bool = False):
    query = update.callback_query
    await query.answer() 
    data = context.user_data
    player_name = query.data
    data[state_id] = player_name
    if team in data:
        data[team].append(player_name)
    else:
        data[team] = [player_name]

    if not is_last_player:
        selected_players = data.get("A", []) + data.get("B", [])
        available_players = list(set(REGISTERED_PLAYERS) - set(selected_players))
        msg = f"Selected players: {', '.join(selected_players)}.\n\n" + text
        await query.edit_message_text(
            msg,
            reply_markup=get_player_keyboard(available_players)
        )
    else:
        await query.edit_message_text(f"Who won?", reply_markup=get_teams_keyboard(data))
    return state_id + 1

async def get_score(update:Update, context:ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer() 
    data = context.user_data
    team = query.data

    if team == "A":
        data["score_A"] = 10
    else:
        data["score_B"] = 10
    await query.edit_message_text(f"Winning team: {team}🏆\n\nWhat was the score of the losing team?")
    return END


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await context.bot.send_message(
        chat_id=update.effective_chat.id,
        text="I'm a bot, please talk to me!"
    )



async def add_player(update: Update, context: ContextTypes.DEFAULT_TYPE):
    player = context.args[0]

    with Session(engine) as session:
        with session.begin():
            players = session.query(Player.name).all()
            players = [p[0] for p in players]
            if player in players:
                await context.bot.send_message(chat_id=update.effective_chat.id, text="Player {} already exists!".format(player))
            else:
                stmt = insert(Player).values(name=player, elo=2000)
                session.execute(stmt)
                await context.bot.send_message(chat_id=update.effective_chat.id, text="Player {} added".format(player))


async def finish(update: Update, context: ContextTypes.DEFAULT_TYPE):
    data = context.user_data
    fail_team_score = update.message.text
    data = context.user_data

    if "score_A" in data:
        data["score_B"] = fail_team_score
    else:
        data["score_A"] = fail_team_score
    
    summary = (
        f"Match Recorded! 🏆\n"
        f"Team A: {', '.join(data['A'])}\n"
        f"Team B: {', '.join(data['B'])}\n"
        f"Score: {data['score_A']}-{data['score_B']}"
    )
    
    await update.message.reply_text(summary)
    context.user_data.clear() 
    return ConversationHandler.END

async def cancel(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data.clear()
    await update.message.reply_text("Match recording cancelled.")
    return ConversationHandler.END


if __name__ == '__main__':
    application = ApplicationBuilder().token(TOKEN).build()
    
    start_handler = CommandHandler('start', start)
    add_handler = CommandHandler('add_player', add_player)

    get_p1a = partial(get_player, state_id = A1, team="A", text = "Who is the player 2 of team A?")
    get_p2a = partial(get_player, state_id = A2, team="A", text = "Who is the player 1 of team B?")
    get_p1b = partial(get_player, state_id = B1, team="B", text = "Who is the player 2 of team B?")
    get_p2b = partial(get_player, state_id = B2, team="B", is_last_player=True)

    conv_handler = ConversationHandler(
        entry_points=[CommandHandler("addmatch", start_match)],
        states={
            A1: [CallbackQueryHandler(get_p1a)],
            A2: [CallbackQueryHandler(get_p2a)],
            B1: [CallbackQueryHandler(get_p1b)],
            B2: [CallbackQueryHandler(get_p2b)],
            SCORE: [CallbackQueryHandler(get_score)],
            END: [MessageHandler(filters.TEXT & ~filters.COMMAND, finish)],
        },
        fallbacks=[CommandHandler("cancel", cancel)],
)

    application.add_handler(start_handler)
    application.add_handler(add_handler)
    application.add_handler(conv_handler)

    
    application.run_polling()