import json
from datetime import datetime, timedelta

from jose import ExpiredSignatureError, jwt, JWTError

from app.configs.logging_settings import get_logger
from app.configs.settings import jwt_settings
from app.exceptions.unauthorized_401 import InvalidTokenException, TokenExpiredException
from app.schemas.jwt import TokenData, TokenDataCreate, Tokens, TokenType

logger = get_logger(__name__)


def verify_token(token: str) -> TokenData:
    try:
        payload: dict = jwt.decode(token=token,
                                   key=jwt_settings.secret_key,
                                   algorithms=jwt_settings.algorithm)
    except ExpiredSignatureError as e:
        raise TokenExpiredException(log_message=f'ExpiredSignatureError: {e}', logger=logger)

    except JWTError as e:
        raise InvalidTokenException(log_message=f'JWTError: {e}', logger=logger)

    token_data_response: TokenData = TokenData(user_id=payload['sub'],
                                               type=payload['type'],
                                               expired_at=datetime.fromtimestamp(payload['exp']))
    return token_data_response


def _encode_token(token_data: TokenDataCreate, expired_at: datetime) -> str:
    token_data.exp = expired_at.timestamp()
    token_data_json: str = token_data.model_dump_json()
    token_data_dict: dict = json.loads(token_data_json)
    token: str = jwt.encode(claims=token_data_dict,
                            key=jwt_settings.secret_key,
                            algorithm=jwt_settings.algorithm)
    return token


def generate_auth_tokens(token_data: TokenDataCreate) -> Tokens:
    access_token_data: TokenDataCreate = token_data.model_copy()
    access_token_data.type = TokenType.ACCESS
    refresh_token_data: TokenDataCreate = token_data.model_copy()
    refresh_token_data.type = TokenType.REFRESH

    current_datetime = datetime.now()
    access_token_expired_at = current_datetime + timedelta(seconds=jwt_settings.access_token_expire_seconds)
    refresh_token_expired_at = current_datetime + timedelta(seconds=jwt_settings.refresh_token_expire_seconds)

    access_token: str = _encode_token(token_data=access_token_data, expired_at=access_token_expired_at)
    refresh_token: str = _encode_token(token_data=refresh_token_data, expired_at=refresh_token_expired_at)

    tokens: Tokens = Tokens(access_token=access_token, access_token_expired_at=access_token_expired_at,
                            refresh_token=refresh_token, refresh_token_expired_at=refresh_token_expired_at)
    return tokens
