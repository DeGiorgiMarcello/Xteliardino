import asyncio
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup, BotCommand
from telegram.ext import (
    ApplicationBuilder,
    ContextTypes,
    CommandHandler,
    MessageHandler,
    filters,
    ConversationHandler,
    CallbackQueryHandler,
)
import dotenv
import os
from db import (
    get_players,
    insert_player,
    insert_match,
    insert_match_participants,
    get_matches,
    Match,
    get_players_ranking,
    update_players_elo
)
from functools import partial
from datetime import datetime

A1 = 0
A2 = 1
B1 = 2
B2 = 3
SCORE = 4
END = 5

dotenv.load_dotenv()
TOKEN = os.environ.get("BOT_TOKEN")


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await context.bot.send_message(
        chat_id=update.effective_chat.id, text="I'm a bot, please talk to me!"
    )


def get_score_keyboard():
    buttons = [InlineKeyboardButton(str(i), callback_data=str(i)) for i in range(10)]

    grid = [buttons[i : i + 3] for i in range(0, len(buttons), 3)]
    return InlineKeyboardMarkup(grid)


def get_player_keyboard(players: list[str]):
    keyboard = []
    for i in range(0, len(players), 2):
        row = [InlineKeyboardButton(p, callback_data=p) for p in players[i : i + 2]]
        keyboard.append(row)
    return InlineKeyboardMarkup(keyboard)


def get_teams_keyboard(data: dict):
    keyboard = []
    teams = {"A": f"Team A\n {data['A']}", "B": f"Team B\n {data['B']}"}

    row = [InlineKeyboardButton(v, callback_data=k) for k, v in teams.items()]
    keyboard.append(row)
    return InlineKeyboardMarkup(keyboard)


async def start_match(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data["players"] = get_players()
    await update.message.reply_text(
        "Who is Player 1 for Team A?",
        reply_markup=get_player_keyboard(context.user_data["players"]),
    )
    return 0


async def get_player(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE,
    team: str,
    state_id: int,
    text: str = "",
    is_last_player: bool = False,
):
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
        available_players = list(set(data["players"]) - set(selected_players))
        msg = f"Selected players: {', '.join(selected_players)}.\n\n" + text
        await query.edit_message_text(
            msg, reply_markup=get_player_keyboard(available_players)
        )
    else:
        await query.edit_message_text("Who won?", reply_markup=get_teams_keyboard(data))
    return state_id + 1


async def get_score(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    data = context.user_data
    team = query.data

    if team == "A":
        data["score_A"] = 10
    else:
        data["score_B"] = 10
    await query.edit_message_text(
        f"Winning team: {team}🏆\n\nWhat was the score of the losing team?",
        reply_markup=get_score_keyboard(),
    )
    return END


async def add_player(update: Update, context: ContextTypes.DEFAULT_TYPE):
    player = context.args[0]
    if not player:
        await context.bot.send_message(
            chat_id=update.effective_chat.id, text="Please provide a player name."
        )
        return
    players = get_players()

    if player in players:
        await context.bot.send_message(
            chat_id=update.effective_chat.id,
            text="Player {} already exists!".format(player),
        )
    else:
        insert_player(player)
        await context.bot.send_message(
            chat_id=update.effective_chat.id, text="Player {} added".format(player)
        )


async def finish(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    fail_team_score = int(query.data)
    data = context.user_data

    if "score_A" in data:
        data["score_B"] = fail_team_score
        winner = "A"

    else:
        data["score_A"] = fail_team_score
        winner = "B"

    ranking = {p[0]:p[1] for p in get_players_ranking()}
    team_A_elo = sum(ranking[p] for p in data["A"])
    team_B_elo = sum(ranking[p] for p in data["B"])
    score_team_A, score_team_B = compute_delta(team_A_elo, team_B_elo, data["score_A"], data["score_B"])
    score_player_A = round(score_team_A / 2)
    score_player_B = round(score_team_B / 2)


    match_id = insert_match(score_A=data["score_A"], score_B=data["score_B"])
    A_list = [
        ("A", match_id, p, score_player_A, True if winner == "A" else False)
        for p in data["A"]
    ]
    B_list = [
        ("B", match_id, p, score_player_B, True if winner == "B" else False)
        for p in data["B"]
    ]

    
    
    for _l in A_list + B_list:
        team = _l[0]
        match_id = _l[1]
        player_id = _l[2]
        prize_won = _l[3]
        won = _l[4]

        insert_match_participants(team, match_id, player_id, prize_won, won)
        current_elo = ranking[player_id]
        new_elo = current_elo + prize_won
        update_players_elo(player_id, new_elo)

    summary = (
        f"Match Recorded! 🏆\n"
        f"Team A: {', '.join(data['A'])}\n"
        f"Team B: {', '.join(data['B'])}\n"
        f"Score: {data['score_A']}-{data['score_B']}"
    )

    await query.edit_message_text(summary)
    context.user_data.clear()
    return ConversationHandler.END


async def cancel(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data.clear()
    await update.message.reply_text("Match recording cancelled.")
    return ConversationHandler.END


async def show_todays_match(update: Update, context: ContextTypes.DEFAULT_TYPE):
    matches = get_matches(date=datetime.today().date())
    if matches:
        matches_summary = [show_match(m) for m in matches]
        matches_summary = "\n\=\=\=\=\=\=\=\n".join(matches_summary)
        await context.bot.send_message(
            chat_id=update.effective_chat.id,
            text=f"Here today's matches:\n{matches_summary}",
            parse_mode="MarkdownV2",
        )
    else:
        await context.bot.send_message(
            chat_id=update.effective_chat.id, text=f"No matches for today!"
        )


def compute_delta(
    teamA_elo: int, teamB_elo: int, scoreA: int, scoreB: int, K: int = 50
):
    Fa = (teamB_elo - teamA_elo) / 400
    Ea = 1 / (1 + 10**Fa)
    Sa = 0.5 + 0.05 * (scoreA - scoreB)
    delta = K * (Sa - Ea)
    return [delta, -delta]


def show_match(m: Match) -> str:
    date = m.date.strftime("%Y\-%m\-%d")
    score_team_A = m.score_team_A
    score_team_B = m.score_team_B
    participants = {"A": [], "B": []}
    for p in m.participants:
        participants[p.team_id].append(p.player_id)

    winner = "A" if score_team_A > score_team_B else "B"
    return (
        f"Date: *{date}*\n"
        f"Winner: *Team {winner}* 🏆\n"
        f"Team A: *{', '.join(participants['A'])}*\n"
        f"Team B: *{', '.join(participants['B'])}*\n"
        f"Score: *{score_team_A}\-{score_team_B}*"
    )


async def show_all_matches(update: Update, context: ContextTypes.DEFAULT_TYPE):
    matches = get_matches()
    if matches:
        matches_summary = [show_match(m) for m in matches]
        matches_summary = "\n\=\=\=\=\=\=\=\n".join(matches_summary)
        await context.bot.send_message(
            chat_id=update.effective_chat.id,
            text=f"Here all the matches:\n{matches_summary}",
        )
    else:
        await context.bot.send_message(
            chat_id=update.effective_chat.id, text=f"No matches recorded", parse_mode="MarkdownV2"
        )


async def post_init(application):
    commands = [
        BotCommand("start", "Start the bot"),
        BotCommand("todays_matches", "Get todays matches"),
        BotCommand("all_matches", "Get all matches recorder"),
        BotCommand("add_player", "Add a new player"),
        BotCommand("add_match", "Add a new match"),
        BotCommand("cancel", "Stop the 'add_match' command"),
        BotCommand("ranking", "Show the ranking"),

    ]
    await application.bot.set_my_commands(commands)

async def show_ranking(update: Update, context: ContextTypes.DEFAULT_TYPE):
    ranking = get_players_ranking()
    emoji = {1: "🥇", 2: "🥈", 3: "🥉"}
    if ranking:
        ranking_text = "Current Player Rankings:\n\n"
        for i, (name, elo) in enumerate(ranking, start=1):
            ranking_text += f"{emoji.get(i,' ')}{i}. {name} - ELO: {elo}\n"
        await context.bot.send_message(
            chat_id=update.effective_chat.id, text=ranking_text
        )
    else:
        await context.bot.send_message(
            chat_id=update.effective_chat.id, text="No players found."
        )

if __name__ == "__main__":
    application = ApplicationBuilder().token(TOKEN).post_init(post_init).build()

    start_handler = CommandHandler("start", start)
    add_handler = CommandHandler("add_player", add_player)
    show_todays_match_handler = CommandHandler("todays_matches", show_todays_match)
    show_all_match_handler = CommandHandler("all_matches", show_all_matches)
    show_ranking_handler = CommandHandler("ranking", show_ranking)

    get_p1a = partial(
        get_player, state_id=A1, team="A", text="Who is the player 2 of team A?"
    )
    get_p2a = partial(
        get_player, state_id=A2, team="A", text="Who is the player 1 of team B?"
    )
    get_p1b = partial(
        get_player, state_id=B1, team="B", text="Who is the player 2 of team B?"
    )
    get_p2b = partial(get_player, state_id=B2, team="B", is_last_player=True)

    conv_handler = ConversationHandler(
        entry_points=[CommandHandler("add_match", start_match)],
        states={
            A1: [CallbackQueryHandler(get_p1a)],
            A2: [CallbackQueryHandler(get_p2a)],
            B1: [CallbackQueryHandler(get_p1b)],
            B2: [CallbackQueryHandler(get_p2b)],
            SCORE: [CallbackQueryHandler(get_score)],
            END: [CallbackQueryHandler(finish)],
        },
        fallbacks=[CommandHandler("cancel", cancel)],
    )

    application.add_handler(start_handler)
    application.add_handler(add_handler)
    application.add_handler(conv_handler)
    application.add_handler(show_todays_match_handler)
    application.add_handler(show_all_match_handler)
    application.add_handler(show_ranking_handler)

    application.run_polling()
