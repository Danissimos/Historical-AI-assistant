from dataclasses import dataclass
from pathlib import Path

from dotenv import load_dotenv


# Корень проекта: каталог, содержащий config/
BASE_DIR = Path(__file__).resolve().parents[1]

# Оставляем твой текущий путь к .env
ENV_PATH = BASE_DIR / "env" / ".env"

load_dotenv(dotenv_path=ENV_PATH, override=False)


@dataclass(frozen=True)
class Settings:
    model_name: str = "qwen3:8b"
    temperature: float = 0.0

    # Langfuse
    langfuse_enabled: bool = True

    # Пути
    base_dir: Path = BASE_DIR
    env_path: Path = ENV_PATH
    prompts_dir: Path = BASE_DIR / "src" / "prompts"


settings = Settings()