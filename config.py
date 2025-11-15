from pydantic_settings import BaseSettings, SettingsConfigDict
from pydantic import BaseModel
from pathlib import Path


class BotSettings(BaseModel):
    token: str
    username: str
    skip_updates: bool


class DatabaseSettings(BaseModel):
    database: str

    @property
    def database_url(self):
        return f"sqlite+aiosqlite:///./{self.database}.sqlite3"


class Config(BaseSettings):
    bot: BotSettings
    database: DatabaseSettings

    admins: list[int]
    hiviews: str | None
    interval: int
    counter: int
    error_notification: bool

    model_config = SettingsConfigDict(env_file=".env", env_nested_delimiter="__")

    @classmethod
    def parse_admins(cls, v):
        if isinstance(v, str):
            if v.startswith("[") and v.endswith("]"):
                # Remove brackets and split by comma
                v = v[1:-1]
            return [int(item.strip()) for item in v.split(",") if item.strip()]
        return v

    def save_env(self, env_file: str | Path | None = None) -> None:
        """
        Save the current configuration to a .env file.
        If env_file is not provided, uses the path from model_config or defaults to '.env'.
        """
        target = Path(env_file or self.model_config.get("env_file", ".env"))

        lines: list[str] = []
        prefix = ""

        def _serialize(obj: BaseModel, _prefix: str) -> None:
            for field_name, field_value in obj:
                full_key = f"{_prefix}{field_name}".upper()
                if isinstance(field_value, BaseModel):
                    _serialize(field_value, f"{full_key}__")
                elif isinstance(field_value, list):
                    # Serialize lists as JSON-like string with brackets
                    lines.append(f"{full_key}={field_value}")
                elif field_value is None:
                    lines.append(f"{full_key}=")
                else:
                    lines.append(f"{full_key}={field_value}")

        _serialize(self, prefix)

        # Ensure directory exists
        target.parent.mkdir(parents=True, exist_ok=True)

        # Write to file
        target.write_text("\n".join(lines), encoding="utf-8")


config = Config()  # noqa
