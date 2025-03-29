from fastapi import APIRouter

from app.api.endpoints import auth, chats, groups, messages, users
from app.schemas.error_response import responses

api_router = APIRouter(responses=responses)

api_router.include_router(auth.router, prefix='/auth', tags=['Auth'])
api_router.include_router(groups.router, prefix='/groups', tags=['Groups'])
api_router.include_router(chats.router, prefix='/chats', tags=['Chats'])
api_router.include_router(messages.router, prefix='/messages', tags=['Messages'])
api_router.include_router(users.router, prefix='/users', tags=['Users'])
