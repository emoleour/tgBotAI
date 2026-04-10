from dataclasses import dataclass
from environs import Env

@dataclass
class TgBot:
    token: str # Токен доступа к телеграм боту

@dataclass
class LogSetting:
    level: str
    format: str

@dataclass
class OllamaApi:
    api_token: str


@dataclass
class Config:
    bot: TgBot
    log: LogSetting
    ollama_token: OllamaApi



def load_config(path: str | None = None) -> Config:
    env = Env()
    env.read_env(path)
    return Config(
        bot=TgBot(token=env('BOT_TOKEN')),
        ollama_token=OllamaApi(api_token=env('OLLAMA_API_KEY')),
        log=LogSetting(level=env('LOG_LEVEL'), format=env('LOG_FORMAT'))
    )

