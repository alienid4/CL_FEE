from dataclasses import dataclass
import os


@dataclass(frozen=True)
class Settings:
    app_name: str = "fee-contract-control"
    app_env: str = "dev"
    app_host: str = "127.0.0.1"
    app_port: int = 8888
    database_path: str = "data/fee_control.db"


def get_settings() -> Settings:
    return Settings(
        app_name=os.getenv("APP_NAME", "fee-contract-control"),
        app_env=os.getenv("APP_ENV", "dev"),
        app_host=os.getenv("APP_HOST", "127.0.0.1"),
        app_port=int(os.getenv("APP_PORT", "8888")),
        database_path=os.getenv("SQLITE_PATH", "data/fee_control.db"),
    )

