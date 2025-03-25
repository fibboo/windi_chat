from app.crud.base import CRUDBase
from app.models import Example
from app.schemas.example import ExampleCreate, ExampleUpdate


class CRUDExample(CRUDBase[Example, ExampleCreate, ExampleUpdate]):
    pass


example_crud = CRUDExample(Example)
