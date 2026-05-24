"""Alembic environment configuration.

This file sets up the migration context so Alembic can autogenerate
migrations based on the SQLAlchemy models defined in
`backend/app/models.py`.

It reads the database URL from the same place the FastAPI app uses:
`backend/app/dependencies.py`. By default that points to a local SQLite
file (`sqlite:///./resume.db`). For production you can set the
`DATABASE_URL` environment variable to a PostgreSQL URL.
"""

import os
import sys
from logging.config import fileConfig

# Ensure the backend package is on the PYTHONPATH
BASE_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
sys.path.append(BASE_DIR)

from app import dependencies, models  # noqa: E402

# this is the Alembic Config object, which provides
# access to the values within the .ini file in use.
from alembic import context
config = context.config

# Interpret the config file for Python logging.
if config.config_file_name is not None:
    fileConfig(config.config_file_name)

# Provide the target metadata for 'autogenerate' support
target_metadata = models.Base.metadata

# Set the sqlalchemy.url dynamically – allow env var override
database_url = os.getenv('DATABASE_URL', dependencies.DATABASE_URL)
config.set_main_option('sqlalchemy.url', database_url)


def run_migrations_offline():
    """Run migrations in 'offline' mode.

    This configures the context with just a URL
    and not an Engine, though an Engine is acceptable
    here as well.  By skipping the Engine creation
    we don't even need a DB driver to be available.
    Calls to context.execute() here emit the given string to the
    script output.
    """
    url = config.get_main_option('sqlalchemy.url')
    context.configure(
        url=url,
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
    )

    with context.begin_transaction():
        context.run_migrations()


def run_migrations_online():
    """Run migrations in 'online' mode.

    In this scenario we create an Engine and associate a connection with the context.
    """
    from sqlalchemy import engine_from_config

    connectable = engine_from_config(
        config.get_section(config.config_ini_section),
        prefix='sqlalchemy.',
        poolclass=None,
    )

    with connectable.connect() as connection:
        context.configure(connection=connection, target_metadata=target_metadata)

        with context.begin_transaction():
            context.run_migrations()

if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
