from typing import List, Optional

from pydantic import BaseModel


class ReviewBase(BaseModel):
    film_name: str
    review: Optional[str] = None
    mark: int


class ReviewCreate(ReviewBase):
    pass


class Review(ReviewBase):
    login: str

    class Config:
        orm_mode = True


class FilmBase(BaseModel):
    name: str
    release_year: Optional[int] = None


class FilmCreate(FilmBase):
    pass


class Film(FilmBase):
    class Config:
        orm_mode = True


class FilmExtended(FilmBase):
    average_mark: Optional[float]
    number_of_marks: Optional[int]
    number_of_reviews: Optional[int]
    reviews: List[Review] = []


class UserBase(BaseModel):
    login: str


class UserCreate(UserBase):
    password: str


class UserInDB(UserBase):
    hashed_password: str


class User(UserBase):
    film_reviews: List[Review] = []

    class Config:
        orm_mode = True
