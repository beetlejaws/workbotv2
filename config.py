from dataclasses import dataclass
from environs import Env
import json

@dataclass
class Bot:
    token: str


@dataclass
class Db:
    name: str
    host: str
    user: str
    password: str

    def __post_init__(self):
        self.url = f'postgresql+asyncpg://{self.user}:{self.password}@{self.host}/{self.name}'


@dataclass
class GoogleService:
    credentials_path: str
    sheets_ids: dict


@dataclass
class Config:
    bot: Bot
    db: Db
    google_service: GoogleService


def load_config(path: str | None = None) -> Config:
    env: Env = Env()
    env.read_env(path)

    return Config(
        bot=Bot(
            token=env('BOT_TOKEN')
        ),
        db=Db(
            name=env('DB_NAME'),
            host=env('DB_HOST'),
            user=env('DB_USER'),
            password=env('DB_PASSWORD')
        ),
        google_service=GoogleService(
            credentials_path=env('GS_CREDENTIALS'),
            sheets_ids=json.loads('SHEETS_IDS')
        )
    )