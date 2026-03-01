from sqlalchemy import (
    create_engine,
    Column,
    Integer,
    String,
    Date,
    ForeignKey,
    Boolean,
    insert,
    select
)
from sqlalchemy.orm import declarative_base, Session
from datetime import datetime

engine = create_engine("sqlite:///biliardino.db")
Base = declarative_base()


class Player(Base):
    __tablename__ = "player"

    name = Column(String, primary_key=True)
    create_at = Column(Date, default=datetime.today())
    elo = Column(Integer, default=2000)


class Match(Base):
    __tablename__ = "match"

    id = Column(Integer, primary_key=True)
    date = Column(Date, default=datetime.today())
    score_team_A = Column(Integer)
    score_team_B = Column(Integer)


class MatchPartecipant(Base):
    __tablename__ = "match_partecipant"

    id = Column(Integer, primary_key=True)
    match_id = Column(ForeignKey(Match.id))
    team_id = Column(String)
    player_id = Column(ForeignKey(Player.name))
    score_in_match = Column(Integer)
    is_winner = Column(Boolean)


Base.metadata.create_all(engine)

def get_current_player_elo(player_id: str):
    with Session(engine) as session:
        with session.begin():
            qry = select(Player.elo).where(Player.name == player_id)
            return session.execute(qry)[0]

def get_players():
    with Session(engine) as session:
        with session.begin():
            players = session.query(Player.name).all()
            return [p[0] for p in players]


def insert_player(player_name: str):
    with Session(engine) as session:
        p =Player(name=player_name)
        session.add(p)
        session.commit()


def insert_match(score_A: int, score_B: int) -> int:
    with Session(engine) as session:
        match = Match(score_team_A=score_A, score_team_B=score_B)
        session.add(match)
        session.commit()
        return match.id

def insert_match_partecipant(
    team_id: str, match_id: str, player_id, score_in_match: int, is_winner: bool
):
    with Session(engine) as session:
        mp = MatchPartecipant(
                team_id=team_id,
                match_id=match_id,
                player_id=player_id,
                is_winner=is_winner,
                score_in_match=score_in_match,
            )
        session.add(mp)
        session.commit()
