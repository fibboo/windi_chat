from uuid import UUID, uuid4

import pytest
from sqlalchemy.ext.asyncio import AsyncSession

from app.configs.logging_settings import LogLevelType
from app.exceptions.conflict_409 import IntegrityException
from app.exceptions.not_fount_404 import EntityNotFound
from app.models.example import Example as ExampleModel
from app.schemas.error_response import ErrorCodeType, ErrorStatusType
from app.schemas.example import Example, ExampleCreate
from app.services import example_service


@pytest.mark.asyncio
async def test_create_example_ok(db_fixture_transaction: AsyncSession):
    # Arrange
    create_data = ExampleCreate(name='test', description='test')

    # Act
    example: Example = await example_service.create_example(db=db_fixture_transaction, create_data=create_data)

    # Assert
    assert example is not None
    assert example.id is not None
    assert example.name == create_data.name
    assert example.description == create_data.description


@pytest.mark.asyncio
async def test_create_example_double(db_fixture_transaction: AsyncSession, db_fixture: AsyncSession):
    # Arrange
    create_data = ExampleCreate(name='test', description='test')
    await example_service.create_example(db=db_fixture, create_data=create_data)
    await db_fixture.commit()

    # Act
    with pytest.raises(IntegrityException) as exc:
        await example_service.create_example(db=db_fixture_transaction, create_data=create_data)

    # Assert
    assert exc.value.status_code == ErrorStatusType.HTTP_409_CONFLICT
    assert exc.value.title == 'Entity integrity error'
    assert exc.value.message == exc.value.log_message
    assert exc.value.log_message == (f'Example integrity error: DETAIL:  '
                                     f'Key (name)=({create_data.name}) already exists.')
    assert exc.value.log_level == LogLevelType.WARNING
    assert exc.value.error_code == ErrorCodeType.INTEGRITY_ERROR


@pytest.mark.asyncio
async def test_get_example_ok(db_fixture: AsyncSession):
    # Arrange
    create_data = ExampleCreate(name='test', description='test')
    created_example: Example = await example_service.create_example(db=db_fixture, create_data=create_data)
    await db_fixture.commit()

    # Act
    example: Example = await example_service.get_example(db=db_fixture, example_id=created_example.id)

    # Assert
    assert example is not None
    assert example.id == created_example.id
    assert example.name == created_example.name
    assert example.description == created_example.description


@pytest.mark.asyncio
async def test_get_example_not_found(db_fixture: AsyncSession):
    # Arrange
    example_id: UUID = uuid4()

    # Act
    with pytest.raises(EntityNotFound) as exc:
        await example_service.get_example(db=db_fixture, example_id=example_id)

    # Assert
    assert exc.value.status_code == ErrorStatusType.HTTP_404_NOT_FOUND
    assert exc.value.title == 'Entity not found'
    search_params = {'id': example_id}
    assert exc.value.log_message == f'{ExampleModel.__name__} not found by {search_params}'
    assert exc.value.message == exc.value.log_message
    assert exc.value.log_level == LogLevelType.ERROR
    assert exc.value.error_code == ErrorCodeType.ENTITY_NOT_FOUND
