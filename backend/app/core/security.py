from passlib.context import CryptContext

from datetime import datetime, timedelta 
from jose import JWTError, jwt, JWTError
from app.core.config import settings

password_context = CryptContext(
    schemes=["bcrypt"],
    deprecated="auto"
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

    return password_context.hash(password)



def verify_password(
    plain_password:str,
    hashed_password:str
):

    return password_context.verify(
        plain_password,
        hashed_password
    )