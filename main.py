import asyncio
from telegram import Update
from telegram.ext import ApplicationBuilder, ContextTypes, CommandHandler
import dotenv
import os
from sqlalchemy.orm import Session
from sqlalchemy import insert
from db import engine, Player

dotenv.load_dotenv()
TOKEN = os.environ.get("BOT_TOKEN")

REGISTERED_PLAYERS = list(range(20))


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



if __name__ == '__main__':
    application = ApplicationBuilder().token(TOKEN).build()
    
    add_handler = CommandHandler('add_player', add_player)
    application.add_handler(add_handler)

    
    application.run_polling()