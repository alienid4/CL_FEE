from dataclasses import dataclass
import os


@dataclass(frozen=True)
class Settings:
    app_name: str
    app_env: str
    app_host: str
    app_port: int
    app_base_url: str
    db_type: str
    sqlite_path: str
    mssql_database: str


def get_settings() -> Settings:
    return Settings(
        app_name=os.getenv("APP_NAME", "fee-contract-control"),
        app_env=os.getenv("APP_ENV", "dev"),
        app_host=os.getenv("APP_HOST", "0.0.0.0"),
        app_port=int(os.getenv("APP_PORT", "8888")),
        app_base_url=os.getenv("APP_BASE_URL", "http://127.0.0.1:8888"),
        db_type=os.getenv("DB_TYPE", "sqlite").lower(),
        sqlite_path=os.getenv("SQLITE_PATH", "./data/dev.db"),
        mssql_database=os.getenv("MSSQL_DATABASE", "FeeContractControl"),
    )
