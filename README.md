# Xteliardino 🤖⚽

## Bot commands

| Command | Description |
|---|---|
| `/start` | Start the bot |
| `/add_match` | Record a new 2v2 match (interactive flow) |
| `/cancel` | Cancel an ongoing `/add_match` session |
| `/add_player <name>` | Register a new player in the system |
| `/todays_matches` | Show all matches played today |
| `/all_matches` | Show the full match history |
| `/ranking` | Display the ELO leaderboard |
| `/stats` | Show win/loss statistics for all players |# Xteliardino 🤖⚽

A Telegram bot for tracking office **biliardino** (foosball) match results — because every goal deserves to be remembered.

---

## What is this?

**Xteliardino** is a lightweight Telegram bot that lets your office team record, track, and consult foosball match results directly from Telegram. No spreadsheets, no sticky notes — just a bot that keeps score.

---

## Features

- 🏆 Record match results through an interactive, step-by-step Telegram conversation
- 👥 Support for 2v2 team matches with player selection via inline buttons
- 📊 ELO-based rating system — every match updates each player's ranking
- 📅 Query today's matches or the full match history (rendered as images)
- 🥇 Live leaderboard with ELO scores
- 📈 Player statistics: win/loss count, win ratio
- 💾 Persistent storage via SQLite (managed with SQLAlchemy)
- ❌ Cancel a match recording in progress at any time

---

## Requirements

- Python 3.10+
- A Telegram Bot Token (obtain one via [@BotFather](https://t.me/BotFather))
- The following Python dependencies:

```
pip install -r requirements.txt
```

---

## Project Structure

```
xteliardino/
├── main.py        # Bot entry point — Telegram handlers and conversation flows
├── db.py          # Database layer — SQLAlchemy models and query functions
├── utils.py       # Helper utilities (e.g. dataframe-to-image rendering)
├── .env           # Environment variables (not committed)
├── requirements.txt
└── README.md
```

---

## Setup

1. **Clone the repository**

```bash
git clone https://github.com/your-org/xteliardino.git
cd xteliardino
```

2. **Install dependencies**

```bash
pip install -r requirements.txt
```

3. **Configure your bot token**

Create a `.env` file in the project root:

```
BOT_TOKEN=your_token_here
```

4. **Run the bot**

```bash
python main.py
```

---

## Bot Commands

| Command | Description |
|---|---|
| `/start` | Welcome message and quick help |
| `/newmatch` | Record a new match result |
| `/leaderboard` | Show the current rankings |
| `/history` | Browse past match results |
| `/stats @player` | Show stats for a specific player |

---

## How to Record a Match

Use `/newmatch` and follow the bot's prompts:

1. Enter the names of the two teams (e.g. `Alice & Bob` vs `Charlie & Dave`)
2. Enter the final score (e.g. `8 - 5`)
3. The result is saved and the leaderboard is updated automatically

---

## Database

Match data is persisted locally in a **SQLite** database (`biliardino.db`) managed via **SQLAlchemy**. The schema consists of three tables:

| Table | Description |
|---|---|
| `player` | Registered players and their current ELO score |
| `match` | Match records with scores for each team and date |
| `match_participant` | Links players to matches with team assignment, ELO delta, and win/loss flag |

### ELO Rating System

After each match, ELO scores are updated using an adapted formula that accounts for the **score margin** and the **pre-match ELO gap** between the two teams. The K-factor is set to `50`.

---

## Contributing

Pull requests are welcome. If you have ideas for new commands, stats, or integrations, open an issue first to discuss the change.

---

## License

MIT — free to use, fork, and deploy in your own office.

---

> *May the best team win. Again and again.*