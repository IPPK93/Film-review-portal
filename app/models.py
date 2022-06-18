from typing import List

from sqlalchemy import CheckConstraint, Column, ForeignKey, Integer, String, and_, text
from sqlalchemy.orm import relationship

from app.database import Base


class Film(Base):
    __tablename__ = 'film'
    film_id = Column(Integer, primary_key=True)
    name = Column(String, nullable=False)
    release_year = Column(Integer)
    reviewers: List['FilmReview'] = relationship(
        'FilmReview', back_populates='film', cascade='all, delete, delete-orphan'
    )


class User(Base):
    __tablename__ = 'user'
    login = Column(String, primary_key=True)
    hashed_password = Column(String, nullable=False)

    film_reviews: List['FilmReview'] = relationship(
        'FilmReview', back_populates='user', cascade='all, delete, delete-orphan'
    )


class FilmReview(Base):
    __tablename__ = 'film_review'
    login: str = Column(ForeignKey(User.login), primary_key=True)
    film_name: str = Column(ForeignKey(Film.name), primary_key=True)
    review = Column(String)
    mark = Column(
        Integer,
        CheckConstraint(and_(text('0 <= mark'), text('mark <= 10'))),
        nullable=False,
    )

    film: Film = relationship('Film', back_populates='reviewers')
    user: User = relationship('User', back_populates='film_reviews')
