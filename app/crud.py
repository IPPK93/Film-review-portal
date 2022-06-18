import hashlib
from typing import List, Optional

from sqlalchemy.orm import Session
from sqlalchemy.sql import func

from . import models, schemas


def get_user_in_db(db: Session, user: schemas.UserInDB) -> Optional[models.User]:
    return (
        db.query(models.User)
        .filter(models.User.login == user.login)
        .filter(models.User.hashed_password == user.hashed_password)
    ).first()


def get_users(db: Session, skip: int = 0, limit: int = 10) -> List[models.User]:
    return db.query(models.User).offset(skip).limit(limit).all()


def create_user(db: Session, user: schemas.UserCreate) -> models.User:
    user_in_db = (
        db.query(models.User.login).filter(models.User.login == user.login).first()
    )
    if user_in_db is not None:
        raise ValueError(f'User with login {user.login} already exists in database')

    password = user.password.encode('utf-8')
    hashed_password = hashlib.sha256(password).hexdigest()

    db_user = models.User(login=user.login, hashed_password=hashed_password)
    db.add(db_user)
    db.commit()
    db.refresh(db_user)
    return db_user


def get_user_review(db: Session, film_name: str, username: str) -> models.FilmReview:
    film = db.query(models.Film.name).filter(models.Film.name == film_name).first()
    if film is None:
        raise ValueError(f'Film with name {film_name} does not exist in database')

    return (
        db.query(models.FilmReview)
        .filter(models.FilmReview.film_name == film_name)
        .filter(models.FilmReview.login == username)
    ).first()


def create_user_review(
    db: Session, username: str, film_review: schemas.ReviewCreate
) -> models.FilmReview:
    film = (
        db.query(models.Film.name)
        .filter(models.Film.name == film_review.film_name)
        .first()
    )
    if film is None:
        raise ValueError(
            f'Film with name {film_review.film_name} does not exist in database'
        )

    review = (
        db.query(models.FilmReview.film_name, models.FilmReview.login)
        .filter(models.FilmReview.film_name == film_review.film_name)
        .filter(models.FilmReview.login == username)
        .first()
    )
    if review is not None:
        raise ValueError(
            f'Film with name {film_review.film_name} have already been reviewed by user {username}'
        )

    db_review = models.FilmReview(**film_review.dict(), login=username)
    db.add(db_review)
    db.commit()
    db.refresh(db_review)
    return db_review


def get_user_reviews(
    db: Session, username: str, skip: int = 0, limit: int = 10
) -> List[models.FilmReview]:
    reviews = (
        db.query(models.FilmReview)
        .filter(models.FilmReview.login == username)
        .offset(skip)
        .limit(limit)
    ).all()
    return reviews


def get_films(db: Session, skip: int = 0, limit: int = 10) -> List[models.Film]:
    return db.query(models.Film).offset(skip).limit(limit).all()


def get_film_reviews(
    db: Session, film_name: str, skip: int = 0, limit: int = 10
) -> List[models.FilmReview]:
    return (
        db.query(models.FilmReview)
        .filter(models.FilmReview.film_name == film_name)
        .offset(skip)
        .limit(limit)
    ).all()


def create_film(db: Session, film: schemas.FilmCreate) -> models.Film:
    film_in_db = (
        db.query(models.Film.name).filter(models.Film.name == film.name).first()
    )
    if film_in_db is not None:
        raise ValueError(f'Film with name {film.name} already exists in database')

    db_film = models.Film(**film.dict())
    db.add(db_film)
    db.commit()
    db.refresh(db_film)
    return db_film


def get_films_filterby_substring(
    db: Session, substring: str, skip: int = 0, limit: int = 10
) -> List[models.Film]:
    return (
        db.query(models.Film)
        .filter(models.Film.name.contains(substring))
        .offset(skip)
        .limit(limit)
    ).all()


def get_films_filterby_release_year(
    db: Session, release_year: int, skip: int = 0, limit: int = 10
) -> List[models.Film]:
    return (
        db.query(models.Film)
        .filter(models.Film.release_year == release_year)
        .offset(skip)
        .limit(limit)
    ).all()


def get_films_filterby_average(
    db: Session, skip: int = 0, limit: int = 10
) -> List[models.Film]:
    return (
        db.query(models.Film)
        .join(models.FilmReview)
        .group_by(models.Film.name)
        .order_by(func.avg(models.FilmReview.mark).desc())
        .offset(skip)
        .limit(limit)
    ).all()


def get_film_info_extended(
    db: Session, film_name: str, skip: int = 0, limit: int = 10
) -> schemas.FilmExtended:
    film = (db.query(models.Film).filter(models.Film.name == film_name)).first()

    if film is None:
        raise ValueError(f'Film with name {film_name} does not exist in database')

    data = (
        db.query(
            func.count(models.FilmReview.mark).label('num_mark'),
            func.avg(models.FilmReview.mark).label('average'),
        )
        .join(models.Film)
        .filter(models.FilmReview.film_name == film_name)
    ).first()

    num_review = (
        db.query(models.FilmReview)
        .filter(models.FilmReview.film_name == film_name)
        .filter(  # pylint: disable=singleton-comparison
            models.FilmReview.review != None  # noqa: E711
        )
    ).count()  # It should be exactly like it is

    average = None
    if data.average is not None:  # set precision to two digits
        average = float(f'{data.average:.2f}')

    extended = schemas.FilmExtended(
        name=film.name,
        release_year=film.release_year,
        average_mark=average,
        number_of_marks=data.num_mark,
        number_of_reviews=num_review,
        reviews=film.reviewers[skip : skip + limit],
    )

    return extended
