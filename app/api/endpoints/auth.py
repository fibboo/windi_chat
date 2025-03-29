from typing import Annotated

from fastapi import APIRouter, Depends
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_db
from app.schemas.jwt import Tokens
from app.services import auth_service

router = APIRouter()


@router.post('/token')
async def login(form_data: Annotated[OAuth2PasswordRequestForm, Depends()],
                db: AsyncSession = Depends(get_db)) -> Tokens:
    tokens: Tokens = await auth_service.login(db=db, form_data=form_data)
    return tokens


@router.post('/token/refresh')
async def refresh_token(token: str,
                        db: AsyncSession = Depends(get_db)) -> Tokens:
    tokens: Tokens = await auth_service.refresh_token(db=db, token=token)
    return tokens
