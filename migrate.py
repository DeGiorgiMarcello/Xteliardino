import pandas as pd
from db import (
    insert_player,
    insert_match,
    insert_match_participants,
    update_players_elo,
)
from main import compute_delta

if __name__ == "__main__":
    df = pd.read_excel("XTEL biliardino 2026.xlsx")
    df.columns = ["id", "DATE", "GA1", "GA2", "SCORE_A", "GB1", "GB2", "SCORE_B"]
    g_cols = ["GA1", "GA2", "GB1", "GB2"]
    df[g_cols] = df[g_cols].apply(lambda x: x.str.strip())
    df["DATE"] = pd.to_datetime(df.DATE, dayfirst=True)

    players = df.GA1.tolist() + df.GA2.tolist() + df.GB1.tolist() + df.GB2.tolist()
    players = list(set([s.strip() for s in players]))
    players_score = {p: 2000 for p in players}

    for player in players:
        try:
            print(f"Inserting player: {player}")
            insert_player(player)
        except Exception as e:
            print(f"Player {player} already exists in the database.")

    for _, match in df.iterrows():
        match_id = match["id"]
        match_players = [match["GA1"], match["GA2"], match["GB1"], match["GB2"]]
        date = match["DATE"]
        match_id = insert_match(
            score_A=match["SCORE_A"], score_B=match["SCORE_B"], date=date
        )
        team_A_elo = sum(players_score[p] for p in [match["GA1"], match["GA2"]])
        team_B_elo = sum(players_score[p] for p in [match["GB1"], match["GB2"]])

        score_team_A, score_team_B = compute_delta(
            team_A_elo, team_B_elo, match["SCORE_A"], match["SCORE_B"]
        )
        player_score_A = round(score_team_A / 2)
        player_score_B = round(score_team_B / 2)

        insert_match_participants(
            team_id="A",
            match_id=match_id,
            player_id=match["GA1"],
            score_in_match=player_score_A,
            is_winner=score_team_A > 0,
        )
        insert_match_participants(
            team_id="A",
            match_id=match_id,
            player_id=match["GA2"],
            score_in_match=player_score_A,
            is_winner=score_team_A > 0,
        )
        insert_match_participants(
            team_id="B",
            match_id=match_id,
            player_id=match["GB1"],
            score_in_match=player_score_B,
            is_winner=score_team_B > 0,
        )
        insert_match_participants(
            team_id="B",
            match_id=match_id,
            player_id=match["GB2"],
            score_in_match=player_score_B,
            is_winner=score_team_B > 0,
        )

        players_score[match["GA1"]] += player_score_A
        players_score[match["GA2"]] += player_score_A
        players_score[match["GB1"]] += player_score_B
        players_score[match["GB2"]] += player_score_B

    for player, score in players_score.items():
        update_players_elo(player, score)
