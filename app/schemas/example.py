from uuid import UUID

from pydantic import BaseModel, ConfigDict, constr


class ExampleBase(BaseModel):
    name: constr(max_length=256)
    description: constr(max_length=2048)


class ExampleCreate(ExampleBase):
    pass


class ExampleUpdate(ExampleBase):
    pass


class Example(ExampleBase):
    id: UUID  # noqa: A003

    model_config = ConfigDict(from_attributes=True)
