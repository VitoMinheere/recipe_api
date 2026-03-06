from fastapi import FastAPI
from sqlmodel import Session, create_engine
from src.app.routes.recipes import router as recipes_router
# from typing import Annotated

sqlite_file_name = "database.db"
sqlite_url = f"sqlite:///{sqlite_file_name}"

connect_args = {"check_same_thread": False}
engine = create_engine(sqlite_url, connect_args=connect_args)


def create_db_and_tables():
    SQLModel.metadata.create_all(engine)


def get_session():
    with Session(engine) as session:
        yield session


# SessionDep = Annotated[Session, Depends(get_session)]

app = FastAPI()
app.include_router(recipes_router, prefix="/recipes")
