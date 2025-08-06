from typing import Type
from db.models import *
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import delete, insert, update
from sqlalchemy.future import select
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
        except Exception as e:
            print(e)
            return False
        
    async def add_telegram_id(self, student_id: int, telegram_id: int) -> None:
        """
        Добавляет в базу данных telegram_id профиля к студенту с указанным student_id
        """
        result = await self.session.execute(
                update(Student).where(Student.id == student_id).values(telegram_id=telegram_id)
            )
        print(result.rowcount)
        if result.rowcount == 0:
            raise ValueError
        await self.session.commit()
        
    async def get_student_id(self, telegram_id: int) -> int | None:
        """
        Возвращает id студента с указанным telegram_id
        """
        result = await self.session.execute(
            select(Student.id).where(Student.telegram_id == telegram_id)
        )
        return result.scalar()
    
    # Возвращает имя и фамилию студента в строковом формате
    async def get_str_full_name(self, telegram_id: int) -> str | None:
        """
        Возвращает имя и фамилию студента с указанным telegram_id в строковом формате
        """
        result = await self.session.execute(
            select(Student.name, Student.surname).where(Student.telegram_id == telegram_id)
        )
        student = result.fetchone()
        if student:
            return f'{student.name} {student.surname}'
    
    async def get_student_class_id(self, telegram_id: int) -> int:
        """
        Возвращает id группы студента с указанным telegram_id
        """
        result = await self.session.execute(
            select(Student.class_id).where(Student.telegram_id == telegram_id)
        )
        class_id = result.scalar()
        if class_id is None:
            raise Exception
        return class_id
    
    async def get_student_variant(self, telegram_id: int) -> int | None:
        """
        Возвращает номер варианта студента с указанным telegram_id
        """
        result = await self.session.execute(
            select(Student.variant).where(Student.telegram_id == telegram_id)
        )
        return result.scalar()
