from uuid import UUID

from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_db, get_db_transaction
from app.schemas.example import Example, ExampleCreate
from app.services import example_service

router = APIRouter()


@router.post('')
async def create_example(create_data: ExampleCreate,
                         db: AsyncSession = Depends(get_db_transaction)) -> Example:
    example: Example = await example_service.create_example(db=db, create_data=create_data)
    return example


@router.get('/{example_id}')
async def get_example(example_id: UUID,
                      db: AsyncSession = Depends(get_db)) -> Example:
    example: Example = await example_service.get_example(db=db, example_id=example_id)
    return example
