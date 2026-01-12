from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, DeclarativeBase, Session

# Banco local SQLite — arquivo clientes.db na raiz do projeto
DATABASE_URL = "sqlite:///./clientes.db"

engine = create_engine(DATABASE_URL, connect_args={"check_same_thread": False})
SessionLocal = sessionmaker(bind=engine, autoflush=False, autocommit=False)

class Base(DeclarativeBase):
    #Base declarativa para os modelos SQLAlchemy.
    pass

def get_db():
    #Dependency de sessão para FastAPI.
    db: Session = SessionLocal()
    try:
        yield db
    finally:
        db.close()


