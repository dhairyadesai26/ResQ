"""
ResQ Web - Database Session & Connection Management
Configures SQLite / PostgreSQL (Supabase) with thread-safe connection pooling,
automatic URL credential sanitization, and connection health recycling.
"""

import urllib.parse
from sqlalchemy import create_engine, event
from sqlalchemy.orm import sessionmaker, Session
from backend.app.core.config import settings


def sanitize_database_url(url: str) -> str:
    """
    Sanitizes database URLs where passwords might contain unescaped characters like '@'.
    RFC 3986 requires special characters in the userinfo part to be percent-encoded.
    """
    if not url or "://" not in url:
        return url

    scheme, remainder = url.split("://", 1)

    # Standardize postgres:// to postgresql:// for SQLAlchemy compatibility
    if scheme == "postgres":
        scheme = "postgresql"

    # If there is an '@' in the remainder, there is userinfo
    if "@" in remainder:
        # The last '@' separates userinfo from host:port/path
        last_at_idx = remainder.rfind("@")
        userinfo = remainder[:last_at_idx]
        host_and_path = remainder[last_at_idx + 1:]

        # Userinfo consists of username:password
        if ":" in userinfo:
            user, password = userinfo.split(":", 1)
            # URL-encode password (unquote first in case it was partially encoded, then quote)
            clean_password = urllib.parse.quote(urllib.parse.unquote(password), safe="")
            clean_user = urllib.parse.quote(urllib.parse.unquote(user), safe="")
            return f"{scheme}://{clean_user}:{clean_password}@{host_and_path}"

    return f"{scheme}://{remainder}"


# Resolve sanitized database URL
db_url = sanitize_database_url(settings.DATABASE_URL)
is_sqlite = db_url.startswith("sqlite")

connect_args = {}
engine_kwargs = {
    "pool_pre_ping": True,
}

if is_sqlite:
    connect_args["check_same_thread"] = False
else:
    # PostgreSQL / Supabase pool configuration
    engine_kwargs["pool_size"] = 10
    engine_kwargs["max_overflow"] = 20
    engine_kwargs["pool_recycle"] = 300
    if "supabase.com" in db_url and "sslmode" not in db_url:
        connect_args["sslmode"] = "require"

engine = create_engine(
    db_url,
    connect_args=connect_args,
    **engine_kwargs,
)

# Enable WAL mode for SQLite to provide high-concurrency read/write
if is_sqlite:
    @event.listens_for(engine, "connect")
    def set_sqlite_pragma(dbapi_connection, connection_record):
        cursor = dbapi_connection.cursor()
        cursor.execute("PRAGMA journal_mode=WAL")
        cursor.execute("PRAGMA synchronous=NORMAL")
        cursor.close()

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


def get_db():
    """Dependency yields thread-safe database session."""
    db: Session = SessionLocal()
    try:
        yield db
    finally:
        db.close()

