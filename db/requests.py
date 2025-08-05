from typing import Type
from db.models import *
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import delete, insert
from utils.utils import convert_value


class Database:
    def __init__(self, session: AsyncSession):
        self.session = session

    @staticmethod
    def get_model_by_table_name(table_name: str) -> Type[Base] | None:
        for mapper in Base.registry.mappers:
            if table_name in [tbl.name for tbl in mapper.tables]:
                return mapper.class_

    async def update_table(self, table_name: str, new_data: list[list]) -> bool:
        model = self.get_model_by_table_name(table_name)
        if model:
            columns = model.__table__.columns
        else:
            return False
        column_names = [col.name for col in model.__table__.columns]

        converted_data = []
        try:
            for row in new_data:
                item = {}
                for index, value in enumerate(row):
                    col_name = column_names[index]
                    col_type = columns[col_name].type
                    item[col_name] = convert_value(value, col_type)
                converted_data.append(item)

            await self.session.execute(
                delete(model)
                )
            await self.session.execute(
                insert(model), converted_data
            )
            await self.session.commit()
            return True
        except:
            return False
