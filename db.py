from sqlalchemy import create_engine, Column, Integer, String, Date, ForeignKey
from sqlalchemy.orm import declarative_base, sessionmaker

engine = create_engine('sqlite:///biliardino.db')
Base = declarative_base()

class Player(Base):
    __tablename__ = 'player'
    
    id = Column(Integer, primary_key=True)
    name = Column(String)
    elo = Column(Integer)



Base.metadata.create_all(engine)





