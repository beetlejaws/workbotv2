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
    
    async def get_class_folder_id(self, class_id: int) -> str | None:
        """
        Возвращает id папки Google диска группы
        """
        result = await self.session.execute(
            select(Class_.folder_id).where(Class_.id == class_id)
        )
        return result.scalar()

    # async def get_courses_for_class(self, class_id: int) -> list[int]:
    #     """
    #     Возвращает список id курсов для указанного id группы
    #     """
    #     result = await self.session.execute(
    #         select(CourseClass.course_id).where(CourseClass.class_id == class_id)
    #     )
    #     return sorted(result.scalars().all())
    
    async def get_course_title(self, course_id: int) -> str | None:
        """
        Возвращает название курса по указанному id курса
        """
        result = await self.session.execute(
            select(Course.title).where(Course.id == course_id)
        )
        return result.scalar()
    
    async def get_class_title(self, class_id: int) -> int | None:
        """
        Возвращает название группы по указанному id группы
        """
        result = await self.session.execute(
            select(Class_.title).where(Class_.id == class_id)
        )
        return result.scalar()
    
    async def get_object_id(self, course_id: int, class_id: int) -> int | None:
        """
        Возвращает id дисциплины для указанного id курса и id группы
        """
        result = await self.session.execute(
            select(CourseClass.id).where(
                CourseClass.course_id == course_id, CourseClass.class_id == class_id
            )
        )
        return result.scalar()
    
    async def get_folder_id_by_object(self, object_id: int) -> str | None:
        result = await self.session.execute(
            select(CourseClass.folder_id).where(CourseClass.id == object_id)
        )
        return result.scalar()
    
    async def get_courses_for_class(self, class_id: int):
    
        query = (
            select(Course.title, CourseClass.id)
            .join(CourseClass, CourseClass.course_id == Course.id)
            .where(CourseClass.class_id == class_id)
            .order_by(CourseClass.id)
        )
        
        result = await self.session.execute(query)
        return result.all()
    
    async def get_lessons_by_period(
    self, 
    object_ids: list[int], 
    start_date: datetime.date, 
    end_date: datetime.date
    ) -> list[dict]:
    
        if not object_ids:
            return []

        query = (
            select(
                Schedule,
                Course.title.label('course_title')
            )
            .join(CourseClass, Schedule.id == CourseClass.id)
            .join(Course, CourseClass.course_id == Course.id)
            .where(
                Schedule.id.in_(object_ids),
                Schedule.date.between(start_date, end_date)
            )
            .order_by(Schedule.date, Schedule.time)
        )
    
        result = await self.session.execute(query)
        lessons_data = result.all()
        
        lessons_list = []
        for schedule, course_title in lessons_data:
            lessons_list.append({
                'id': schedule.id,
                'number': schedule.number,
                'date': schedule.date,
                'time': schedule.time,
                'lesson_title': schedule.title,
                'is_work': schedule.is_work,
                "course_title": course_title
            })

        return lessons_list
    
    async def get_active_tests(self, class_id: int, start_date: datetime.date | None = None, end_date: datetime.date | None = None):
        if start_date is None:
            now = datetime.datetime.now()
            query = (
                select(Test, Course.title.label('course_title')
                )
                .join(Course, Test.course_id == Course.id)
                .join(CourseClass, Test.course_id == CourseClass.course_id)
                .where(
                    CourseClass.class_id == class_id,
                    Test.start_date <= now.date(),
                    Test.start_time <= now.time(),
                    Test.end_date >= now.date(),
                    Test.end_time >= now.time()
                    )
                .order_by(Test.end_date, Test.end_time)
            )
        else:
            query = (
                select(Test, Course.title.label('course_title')
                )
                .join(Course, Test.course_id == Course.id)
                .join(CourseClass, Test.course_id == CourseClass.course_id)
                .where(
                    CourseClass.class_id == class_id,
                    Test.end_date >= start_date,
                    Test.end_date <= end_date,
                    )
                .order_by(Test.end_date, Test.end_time)
            )

        result = await self.session.execute(query)
        tests_data = result.all()

        tests_dict = {}
        for test, course_title in tests_data:
            tests_dict[test.id] = {
                'course_title': course_title,
                'test_title': test.title,
                'end_date': test.end_date,
                'end_time': test.end_time,
                'public_folder_id': test.public_folder_id,
                'private_folder_id': test.private_folder_id
            }
        return tests_dict