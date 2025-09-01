from pydantic import BaseModel, computed_field, ConfigDict
import datetime

class StudentUser(BaseModel):
    id: int
    telegram_id: int
    name: str
    surname: str
    class_id: int
    variant: int
    class_title: str | int = None
    lesson_sub: bool | None
    deadlines_sub: bool | None
    subject_ids: list[int] = None

    @computed_field
    def full_name(self) -> str:
        return f'{self.name} {self.surname}'
    
    model_config = ConfigDict(from_attributes=True)


class Subject(BaseModel):
    id: int
    course_id: int
    class_id: int
    folder_id: str
    course_title: str = None
    class_title: int = None

    model_config = ConfigDict(from_attributes=True)


class Lesson(BaseModel):
    id: int
    number: int
    date: datetime.date
    time: datetime.time
    title: str
    is_work: bool | None
    course_title: str = None
    folder_id: str = None

    model_config = ConfigDict(from_attributes=True)

    @computed_field
    def short_name(self) -> str:
        return (self.course_title + f' Занятие {self.number}' if self.number > 9 else f'Занятие 0{self.number}')

    @computed_field
    def file_name(self) -> str:
        return (f'Занятие {self.number}' if self.number > 9 else f'Занятие 0{self.number}') + '.pdf'
    
    def __str__(self) -> str:
        sign = '❗️ ' if self.is_work else ''
        day = datetime.date.strftime(self.date, '%d.%m')
        start_time = datetime.time.strftime(self.time, '%H:%M')
        return f'{sign}{day} {start_time} {self.course_title} Занятие № {self.number}\n{self.title}'
    

class Test(BaseModel):
    id: int
    course_id: int
    title: str
    start_date: datetime.date
    start_time: datetime.time
    end_date: datetime.date
    end_time: datetime.time
    public_folder_id: str
    private_folder_id: str
    course_title: str = None

    model_config = ConfigDict(from_attributes=True)

    def __str__(self) -> str:
        day = datetime.date.strftime(self.end_date, '%d.%m')
        end_time = datetime.time.strftime(self.end_time, '%H:%M')
        return f'{day} {end_time} {self.course_title} {self.title}'

    #     day = date.strftime(test['end_date'], '%d.%m')
    # end_time = time.strftime(test['end_time'], '%H:%M')
    # course_title = test['course_title']
    # test_title = test['test_title']
    # return f'{day} {end_time}\n{course_title} {test_title}'

