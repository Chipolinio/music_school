from logging.config import fileConfig
from pathlib import Path
import sys
from dotenv import load_dotenv

from sqlalchemy import engine_from_config, pool
from sqlalchemy.engine import Connection

from alembic import context

# Добавляем проект в path для импорта настроек
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

# Загружаем .env с переопределением переменных окружения
load_dotenv(dotenv_path=Path(__file__).resolve().parents[1] / ".env", override=True)

from settings import settings
from src.models.Base import BaseModel
from src.models.User import User  # noqa: F401
from src.models.Room import Room  # noqa: F401
from src.models.LessonSlot import LessonSlot  # noqa: F401
from src.models.LessonBooking import LessonBooking  # noqa: F401
from src.models.RehearsalBooking import RehearsalBooking  # noqa: F401
from src.models.Notification import Notification  # noqa: F401

# this is the Alembic Config object, which provides
# access to the values within the .ini file in use.
config = context.config

# Устанавливаем URL базы данных из настроек (синхронный для миграций)
config.set_main_option("sqlalchemy.url", settings.SYNC_DATABASE_URL)

# Interpret the config file for Python logging.
# This line sets up loggers basically.
if config.config_file_name is not None:
    fileConfig(config.config_file_name)

# add your model's MetaData object here
# for 'autogenerate' support
target_metadata = BaseModel.metadata


def run_migrations_offline() -> None:
    """Run migrations in 'offline' mode."""
    url = config.get_main_option("sqlalchemy.url")
    context.configure(
        url=url,
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
        render_as_batch=True,
    )

    with context.begin_transaction():
        context.run_migrations()


def run_migrations_online() -> None:
    """Run migrations in 'online' mode."""
    connectable = engine_from_config(
        config.get_section(config.config_ini_section, {}),
        prefix="sqlalchemy.",
        poolclass=pool.NullPool,
    )

    with connectable.connect() as connection:
        context.configure(
            connection=connection,
            target_metadata=target_metadata,
            render_as_batch=True,
        )

        with context.begin_transaction():
            context.run_migrations()


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
