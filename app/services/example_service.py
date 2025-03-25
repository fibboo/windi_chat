from uuid import UUID

from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from app.configs.logging_settings import get_logger
from app.crud.example import example_crud
from app.exceptions.conflict_409 import IntegrityException
from app.exceptions.not_fount_404 import EntityNotFound
from app.schemas.example import Example, ExampleCreate
from app.models.example import Example as ExampleModel

logger = get_logger(__name__)


async def create_example(db: AsyncSession, create_data: ExampleCreate) -> Example:
    try:
        expense_db: ExampleModel = await example_crud.create(db=db, obj_in=create_data)

    except IntegrityError as exc:
        raise IntegrityException(entity=ExampleModel, exception=exc, logger=logger)

    example: Example = Example.model_validate(expense_db)
    return example


async def get_example(db: AsyncSession, example_id: UUID) -> Example:
    expense_db: ExampleModel | None = await example_crud.get_or_none(db=db, id=example_id)

    if expense_db is None:
        raise EntityNotFound(entity=ExampleModel, search_params={'id': example_id}, logger=logger)

    example: Example = Example.model_validate(expense_db)
    return example
