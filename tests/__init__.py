import testing.postgresql
import settings


Postgresql = testing.postgresql.PostgresqlFactory(cache_initialized_db=False)
postgresql = Postgresql()
settings.DB_URI = postgresql.url()
