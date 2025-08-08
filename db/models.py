from sqlalchemy.orm import DeclarativeBase
from sqlalchemy.ext.asyncio import AsyncAttrs
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy import ForeignKey, BigInteger
import datetime


class Base(DeclarativeBase, AsyncAttrs):
    pass

class Course(Base):
    __tablename__ = 'courses'

    id: Mapped[int] = mapped_column(primary_key=True)
    title: Mapped[str] = mapped_column()

    classes: Mapped[list['CourseClass']] = relationship(back_populates='course')



class Class_(Base):
    __tablename__ = 'classes'

    id: Mapped[int] = mapped_column(primary_key=True)
    title: Mapped[int] = mapped_column()
    folder_id: Mapped[str] = mapped_column()

    courses: Mapped[list['CourseClass']] = relationship(back_populates='class_')


class  CourseClass(Base):
    __tablename__ = 'courses_and_classes'

    id: Mapped[int] = mapped_column(primary_key=True)
    course_id: Mapped[int] = mapped_column(ForeignKey('courses.id'))
    class_id: Mapped[int] = mapped_column(ForeignKey('classes.id'))
    folder_id: Mapped[str] = mapped_column()

    course: Mapped['Course'] = relationship(back_populates='classes')
    class_: Mapped['Class_'] = relationship(back_populates='courses')


class Student(Base):
    __tablename__ = 'students'

    id: Mapped[int] = mapped_column(primary_key=True)
    telegram_id: Mapped[int] = mapped_column(BigInteger, nullable=True)
    name: Mapped[str] = mapped_column()
    surname: Mapped[str] = mapped_column()
    class_id: Mapped[int] = mapped_column(ForeignKey('classes.id'))
    variant: Mapped[int] = mapped_column()


class Test(Base):
    __tablename__ = 'tests'

    id: Mapped[int] = mapped_column(primary_key=True)
    course_id: Mapped[int] = mapped_column(ForeignKey('courses.id'))
    title: Mapped[str] = mapped_column()
    start_date: Mapped[datetime.date] = mapped_column()
    start_time: Mapped[datetime.time] = mapped_column()
    end_date: Mapped[datetime.date] = mapped_column()
    end_time: Mapped[datetime.time] = mapped_column()


class Schedule(Base):
    __tablename__ = 'schedule'

    id: Mapped[int] = mapped_column(ForeignKey('courses_and_classes.id'), primary_key=True)
    number: Mapped[int] = mapped_column(primary_key=True)
    date: Mapped[datetime.date] = mapped_column()
    time: Mapped[datetime.time] = mapped_column()
    title: Mapped[str] = mapped_column()
    is_work: Mapped[bool] = mapped_column(nullable=True)
