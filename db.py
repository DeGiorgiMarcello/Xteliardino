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
from sqlalchemy.orm import declarative_base, Session, relationship, selectinload
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
    participants = relationship("MatchParticipant", back_populates="match")


class MatchParticipant(Base):
    __tablename__ = "match_participant"

    id = Column(Integer, primary_key=True)
    match_id = Column(ForeignKey(Match.id))
    team_id = Column(String)
    player_id = Column(ForeignKey(Player.name))
    score_in_match = Column(Integer)
    is_winner = Column(Boolean)
    match = relationship("Match", back_populates="participants")


Base.metadata.create_all(engine)

def get_current_player_elo(player_id: str):
    with Session(engine) as session:
        with session.begin():
            qry = select(Player.elo).where(Player.name == player_id)
            return session.execute(qry)[0]

from sqlalchemy import select

def get_players():
    with Session(engine) as session:
        statement = select(Player.name)
        return session.scalars(statement).all()

def get_players_ranking():
    with Session(engine) as session:
        statement = select(Player.name, Player.elo).order_by(Player.elo.desc())
        return session.execute(statement).all()
        


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

def insert_match_participants(
    team_id: str, match_id: str, player_id, score_in_match: int, is_winner: bool
):
    with Session(engine) as session:
        mp = MatchParticipant(
                team_id=team_id,
                match_id=match_id,
                player_id=player_id,
                is_winner=is_winner,
                score_in_match=score_in_match,
            )
        session.add(mp)
        session.commit()

def get_matches(date: datetime = None):
    with Session(engine) as session:
        stmnt = select(Match).options(selectinload(Match.participants))
        
        if date:
            stmnt = stmnt.where(Match.date == date)
        return session.scalars(stmnt).all()

