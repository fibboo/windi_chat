import bcrypt
from fastapi_pagination import Page
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from app.configs.logging_settings import get_logger
from app.crud.user import user_crud
from app.exceptions.conflict_409 import IntegrityException
from app.exceptions.not_fount_404 import EntityNotFound
from app.models.user import User as UserModel
from app.schemas.user import User, UserCreate, UserCreateRequest, UserRequest

logger = get_logger(__name__)


async def create_user(db: AsyncSession, create_data: UserCreateRequest) -> User:
    hashed_password: str = bcrypt.hashpw(create_data.password.encode(), bcrypt.gensalt()).decode()
    create_data: UserCreate = UserCreate(username=create_data.username, password=hashed_password)
    try:
        user_db: UserModel = await user_crud.create(db=db, obj_in=create_data)

    except IntegrityError as exc:
        raise IntegrityException(entity=UserModel, exception=exc, logger=logger)

    user: User = User.model_validate(user_db)
    return user


async def get_user(db: AsyncSession, user_id: int) -> User:
    user_db: UserModel | None = await user_crud.get_or_none(db=db, id=user_id)
    if user_db is None:
        raise EntityNotFound(entity=UserModel, search_params={'id': user_id}, logger=logger)

    user: User = User.model_validate(user_db)
    return user


async def get_users(db: AsyncSession, request: UserRequest, current_user_id: int | None = None) -> Page[User]:
    users_db: Page[UserModel] = await user_crud.get_users(db=db, request=request, current_user_id=current_user_id)
    users: Page[User] = Page[User].model_validate(users_db)
    return users
