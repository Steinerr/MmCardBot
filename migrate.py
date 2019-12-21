import os

from yoyo import get_backend, read_migrations

backend = get_backend(os.environ.get('DATABASE_URL'))
migrations = read_migrations('migrations')
with backend.lock():
    backend.apply_migrations(backend.to_apply(migrations))
