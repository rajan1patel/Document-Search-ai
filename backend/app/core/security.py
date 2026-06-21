import bcrypt

from datetime import datetime, timedelta 
from jose import JWTError, jwt, JWTError
from app.core.config import settings


def _validate_password_length(password: str):
    password_bytes = len(password.encode("utf-8"))

    if password_bytes > 72:
        raise ValueError(
            f"password is {password_bytes} bytes; bcrypt only accepts up to 72 bytes"
        )


def create_access_token(data:dict):

    to_encode=data.copy()


    expire=datetime.utcnow()+timedelta(
        minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES
    )


    to_encode.update(
        {
          "exp":expire
        }
    )


    return jwt.encode(
        to_encode,
        settings.JWT_SECRET,
        algorithm=settings.JWT_ALGORITHM
    )



def decode_access_token(token:str):

    try:

        payload = jwt.decode(
            token,
            settings.JWT_SECRET,
            algorithms=[
                settings.JWT_ALGORITHM
            ]
        )

        return payload


    except JWTError:

        return None

def hash_password(password:str):

    _validate_password_length(password)

    password_bytes = password.encode("utf-8")

    return bcrypt.hashpw(
        password_bytes,
        bcrypt.gensalt()
    ).decode("utf-8")



def verify_password(
    plain_password:str,
    hashed_password:str
):

    _validate_password_length(plain_password)

    return bcrypt.checkpw(
        plain_password.encode("utf-8"),
        hashed_password.encode("utf-8")
    )
