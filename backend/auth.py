import bcrypt
import jwt
import uuid
from datetime import datetime, timedelta
import os

# JWT Configuration — read from environment
JWT_SECRET_KEY = os.environ.get("JWT_SECRET_KEY") or os.environ.get("SECRET_KEY")
if not JWT_SECRET_KEY:
    raise RuntimeError(
        "Thiếu biến môi trường JWT_SECRET_KEY (hoặc SECRET_KEY) cho JWT. "
        "Hãy tạo key mạnh: python -c \"import secrets; print(secrets.token_hex(32))\""
    )
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 60           # 1 hour
REFRESH_TOKEN_EXPIRE_MINUTES = 60 * 24 * 7  # 7 days


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Compare plaintext password against bcrypt hash."""
    try:
        password_bytes = plain_password.encode('utf-8')
        hash_bytes = hashed_password.encode('utf-8')
        return bcrypt.checkpw(password_bytes, hash_bytes)
    except Exception as e:
        print("Verify password error:", e)
        return False


def get_password_hash(password: str) -> str:
    """Hash password with bcrypt, cost factor 10 (production-grade)."""
    password_bytes = password.encode('utf-8')
    salt = bcrypt.gensalt(rounds=10)
    hashed_bytes = bcrypt.hashpw(password_bytes, salt)
    return hashed_bytes.decode('utf-8')


def create_access_token(data: dict) -> str:
    """Create a short-lived access token (1 hour)."""
    to_encode = data.copy()
    expire = datetime.utcnow() + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    to_encode.update({
        "exp": expire,
        "jti": str(uuid.uuid4()),
        "type": "access"
    })
    return jwt.encode(to_encode, JWT_SECRET_KEY, algorithm=ALGORITHM)


def create_refresh_token(data: dict) -> str:
    """Create a long-lived refresh token (7 days)."""
    to_encode = data.copy()
    expire = datetime.utcnow() + timedelta(minutes=REFRESH_TOKEN_EXPIRE_MINUTES)
    to_encode.update({
        "exp": expire,
        "jti": str(uuid.uuid4()),
        "type": "refresh"
    })
    return jwt.encode(to_encode, JWT_SECRET_KEY, algorithm=ALGORITHM)


def decode_access_token(token: str) -> dict | None:
    """Decode and validate a JWT token. Returns payload or None."""
    try:
        payload = jwt.decode(token, JWT_SECRET_KEY, algorithms=[ALGORITHM])
        return payload
    except jwt.ExpiredSignatureError:
        return None
    except jwt.PyJWTError:
        return None


def is_token_blacklisted(jti: str, db_session) -> bool:
    """Check if a token's JTI has been revoked."""
    from db.models import TokenBlacklist
    return db_session.query(TokenBlacklist).filter(TokenBlacklist.jti == jti).first() is not None


def blacklist_token(jti: str, expires_at: datetime, db_session) -> None:
    """Add a token's JTI to the blacklist."""
    from db.models import TokenBlacklist
    entry = TokenBlacklist(jti=jti, expires_at=expires_at)
    db_session.add(entry)
    db_session.commit()


def cleanup_expired_blacklist(db_session) -> None:
    """Remove expired entries from the blacklist to keep the table small."""
    from db.models import TokenBlacklist
    db_session.query(TokenBlacklist).filter(
        TokenBlacklist.expires_at < datetime.utcnow()
    ).delete()
    db_session.commit()
