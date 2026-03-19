from sqlalchemy import (
    create_engine,
    Column,
    Integer,
    String,
    Date,
    ForeignKey,
    Boolean,
    update,
    select,
    func,
    cast,
    desc,
)
from sqlalchemy.orm import declarative_base, Session, relationship, selectinload
from datetime import datetime
import pandas as pd

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


def get_players():
    with Session(engine) as session:
        statement = select(Player.name)
        return session.scalars(statement).all()


def get_players_ranking():
    with Session(engine) as session:
        statement = select(Player.name, Player.elo).order_by(Player.elo.desc())
        return session.execute(statement).all()


def update_players_elo(player_id: str, new_elo: int):
    with Session(engine) as session:
        with session.begin():
            stmt = update(Player).where(Player.name == player_id).values(elo=new_elo)
            session.execute(stmt)


def insert_player(player_name: str):
    with Session(engine) as session:
        p = Player(name=player_name)
        session.add(p)
        session.commit()


def insert_match(score_A: int, score_B: int, date=datetime.today()) -> int:
    with Session(engine) as session:
        match = Match(score_team_A=score_A, score_team_B=score_B, date=date)
        session.add(match)
        session.commit()
        return match.id


def insert_match_participants(
    team_id: str, match_id: str, player_id: str, score_in_match: int, is_winner: bool
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


def get_stats():
    with Session(engine) as session:
        stmnt = (
            select(
                MatchParticipant.player_id,
                func.count(MatchParticipant.is_winner).label("total_matches"),
                func.sum(cast(MatchParticipant.is_winner, Integer)).label(
                    "won_matches"
                ),
                func.round(
                    func.sum(cast(MatchParticipant.is_winner, Integer))
                    * 100
                    / func.count(cast(MatchParticipant.is_winner, Integer))
                ).label("won_ratio"),
            )
            .group_by(MatchParticipant.player_id)
            .order_by(desc("won_ratio"))
        )

        return session.execute(stmnt).mappings().all()


def get_matches(date: datetime = None, as_df=False):
    with Session(engine) as session:
        stmnt = select(Match).options(selectinload(Match.participants))

        if date:
            stmnt = stmnt.where(Match.date == date)
        if as_df:
            matches_df = pd.read_sql(stmnt, session.bind)
            participants_df = pd.read_sql(select(MatchParticipant), session.bind)
            grouped = (
                participants_df.groupby(["match_id", "team_id"])["player_id"]
                .agg(list)
                .reset_index()
            )
            pivoted = grouped.pivot(columns="team_id", index="match_id").reset_index()
            pivoted.columns = [
                f"{col[0]}_{col[1]}" if col[1] != "" else col[0]
                for col in pivoted.columns
            ]

            return matches_df.merge(pivoted, left_on="id", right_on="match_id")
        return session.scalars(stmnt).all()
