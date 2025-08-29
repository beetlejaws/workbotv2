from dataclasses import dataclass
from environs import Env
from datetime import date
import json

@dataclass
class Bot:
    token: str
    admin_id: int
    logging_group_id: int
    info_topic_id: int
    error_topic_id: int


@dataclass
class Db:
    name: str
    host: str
    user: str
    password: str

    def __post_init__(self):
        self.url = f'postgresql+asyncpg://{self.user}:{self.password}@{self.host}/{self.name}'


@dataclass
class NatsConfig:
    servers: list[str]


@dataclass
class NatsConsumerConfig:
    subject: str
    stream: str
    durable_name: str


@dataclass
class GoogleService:
    credentials_path: str
    sheets_ids: dict

@dataclass
class Calendar:
    first_workday: date
    last_workday: date


@dataclass
class Config:
    bot: Bot
    db: Db
    google_service: GoogleService
    calendar: Calendar
    nats: NatsConfig
    consumer: NatsConsumerConfig


def load_config(path: str | None = None) -> Config:
    env: Env = Env()
    env.read_env(path)
    with open('sheets_ids.json', 'r') as file:
        sheets_ids = json.load(file)

    return Config(
        bot=Bot(
            token=env('BOT_TOKEN'),
            admin_id=int(env('ADMIN_ID')),
            logging_group_id=int(env('LOGGING_GROUP_ID')),
            info_topic_id=int(env('INFO_TOPIC_ID')),
            error_topic_id=int(env('ERROR_TOPIC_ID'))
        ),
        db=Db(
            name=env('DB_NAME'),
            host=env('DB_HOST'),
            user=env('DB_USER'),
            password=env('DB_PASSWORD')
        ),
        nats=NatsConfig(servers=env.list('NATS_SERVERS')),
        consumer = NatsConsumerConfig(
            subject=env('NATS_SUBJECT'),
            stream='NATS_STREAM',
            durable_name=env('NATS_CONSUMER_DURABLE_NAME')
        ),
        google_service=GoogleService(
            credentials_path=env('GS_CREDENTIALS'),
            sheets_ids=sheets_ids
        ),
        calendar=Calendar(
            first_workday=date.fromisoformat(env('FIRST_WORKDAY')),
            last_workday=date.fromisoformat(env('LAST_WORKDAY'))
        )
    )