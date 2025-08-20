from pydantic import BaseModel, computed_field, ConfigDict


class StudentUser(BaseModel):
    id: int
    telegram_id: int
    name: str
    surname: str
    class_id: int
    variant: int
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
