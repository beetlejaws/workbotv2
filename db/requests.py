from typing import Type
from db.models import *
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import delete, insert, update
from sqlalchemy.future import select
from utils.utils import convert_value
from db.views import StudentUser, Subject, Lesson
from db.views import Test as TestView


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
        
    async def add_telegram_id(self, student_id: int, telegram_id: int) -> StudentUser:
        """
        Добавляет в базу данных telegram_id профиля к студенту с указанным student_id и возвращает экземпляр класса StudentUser
        """
        result = await self.session.execute(
                update(Student).where(Student.id == student_id).values(telegram_id=telegram_id, lesson_sub=True, deadlines_sub=True)
            )
        if result.rowcount == 0:
            raise ValueError

        await self.session.commit()
        return await self.get_student_by_telegram_id(telegram_id)
    
    async def change_sub_status(self, student_id: int, mode: str) -> bool:
        if mode == 'lesson':
            result = await self.session.execute(
                select(Student.lesson_sub).where(Student.id == student_id)
            )
            status = result.scalar_one()
            result = await self.session.execute(
                update(Student).where(Student.id == student_id).values(lesson_sub=(not status))
            )
        else:
            result = await self.session.execute(
                select(Student.deadlines_sub).where(Student.id == student_id)
            )
            status = result.scalar_one()
            result = await self.session.execute(
                update(Student).where(Student.id == student_id).values(deadlines_sub=(not status))
            )
        
        await self.session.commit()

        return not status
    
    async def get_sub_lesson_students(self, mode: str):
        if mode == 'lesson':
            result = await self.session.execute(
                select(Student.telegram_id).where(Student.lesson_sub == True)
            )
        else:
            result = await self.session.execute(
                select(Student.telegram_id).where(Student.deadlines_sub == True)
            )
        return result.scalars().all()

    async def get_student_by_telegram_id(self, telegram_id):
        result = await self.session.execute(
            select(Student, Class_.title)
            .join(Class_, Class_.id == Student.class_id)
            .where(Student.telegram_id == telegram_id)
        )

        row = result.first()
        if not row:
            return None

        student, class_title = row

        subject_ids_result = await self.session.execute(
            select(CourseClass.id).where(CourseClass.class_id == student.class_id)
        )
        subject_ids = subject_ids_result.scalars().all()

        student_user = StudentUser.model_validate(student)
        student_user.class_title = class_title
        student_user.subject_ids = subject_ids

        return student_user
    
    async def get_student_by_id(self, student_id):
        student_result = await self.session.execute(
            select(Student).where(Student.id == student_id)
        )
        student = student_result.scalar_one_or_none()

        if student is None:
            return None

        subject_ids_result = await self.session.execute(
            select(CourseClass.id).where(CourseClass.class_id == student.class_id)
        )
        subject_ids = subject_ids_result.scalars().all()

        student_user = StudentUser.model_validate(student)
        student_user.subject_ids = subject_ids

        return student_user
    
    async def get_subjects_by_ids(self, subject_ids: list[int]) -> list[Subject]:
        
        query = (
            select(CourseClass, Course.title, Class_.title)
            .join(Course, Course.id == CourseClass.course_id)
            .join(Class_, Class_.id == CourseClass.class_id)
            .where(CourseClass.id.in_(subject_ids))
            .order_by(CourseClass.id)
        )

        result = await self.session.execute(query)

        subjects_list = []
        for subject_data, course_title, class_title in result.all():
            subject = Subject.model_validate(subject_data)
            subject.course_title = course_title
            subject.class_title = class_title
            subjects_list.append(subject)
        return subjects_list
        
    async def get_student_id(self, telegram_id: int) -> int | None:
        """
        Возвращает id студента с указанным telegram_id
        """
        result = await self.session.execute(
            select(Student.id).where(Student.telegram_id == telegram_id)
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
    
    async def get_lessons_by_period(
        self, 
        subject_ids: list[int], 
        start_date: datetime.date, 
        end_date: datetime.date
    ) -> list[Lesson]:
        
        query = (
            select(Schedule, Course.title, CourseClass.folder_id)
            .join(CourseClass, Schedule.id == CourseClass.id)
            .join(Course, CourseClass.course_id == Course.id)
            .where(
                Schedule.id.in_(subject_ids),
                Schedule.date.between(start_date, end_date)
            )
            .order_by(Schedule.date, Schedule.time)
        )

        result = await self.session.execute(query)
        lessons_data = result.all()

        lessons_list = []
        for schedule, course_title, folder_id in lessons_data:
            lesson = Lesson.model_validate(schedule)
            lesson.course_title = course_title
            lesson.folder_id = folder_id
            lessons_list.append(lesson)

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

        tests_list = []
        for test_orm, course_title in tests_data:
            test = TestView.model_validate(test_orm)
            test.course_title = course_title
            tests_list.append(test)
        return tests_list