import hashlib
import logging
from typing import Generator, List

from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBasicCredentials
from sqlalchemy.orm import Session

from . import app, crud, models, schemas, security
from .database import LocalSession


def get_db() -> Generator[Session, None, None]:
    db = LocalSession()
    try:
        yield db
    finally:
        db.close()


def get_current_username(
    credentials: HTTPBasicCredentials = Depends(security), db: Session = Depends(get_db)
) -> str:
    hashed_password = hashlib.sha256(credentials.password.encode('utf-8')).hexdigest()
    user = schemas.UserInDB(login=credentials.username, hashed_password=hashed_password)
    db_user = crud.get_user_in_db(user=user, db=db)
    if db_user is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail='Incorrect login or password',
            headers={'WWW-Authenticate': 'Basic'},
        )
    return credentials.username


@app.post('/users/', response_model=schemas.User)
def create_user(user: schemas.UserCreate, db: Session = Depends(get_db)) -> models.User:
    try:
        return crud.create_user(db=db, user=user)
    except ValueError as e:
        logging.error(str(e))
        raise HTTPException(status_code=400, detail=str(e)) from e


@app.get(
    '/users/',
    response_model=List[schemas.User],
    dependencies=[Depends(get_current_username)],
)
def read_users(
    skip: int = 0, limit: int = 10, db: Session = Depends(get_db)
) -> List[models.User]:
    return crud.get_users(db, skip, limit)


@app.post('/users/me/reviews/', response_model=schemas.Review)
def create_user_review(
    review: schemas.ReviewCreate,
    username: str = Depends(get_current_username),
    db: Session = Depends(get_db),
) -> models.FilmReview:
    try:
        result = crud.create_user_review(db=db, username=username, film_review=review)
        logging.info('%s %s', result.user, result.film)
        return result
    except ValueError as e:
        logging.error(str(e))
        raise HTTPException(status_code=400, detail=str(e)) from e


@app.get('/users/me/reviews/{film_name}/', response_model=schemas.Review)
def read_user_review(
    film_name: str,
    username: str = Depends(get_current_username),
    db: Session = Depends(get_db),
) -> models.FilmReview:
    try:
        return crud.get_user_review(db, film_name=film_name, username=username)
    except ValueError as e:
        logging.error(str(e))
        raise HTTPException(status_code=400, detail=str(e)) from e


@app.get('/users/me/reviews/', response_model=List[schemas.Review])
def read_user_reviews(
    skip: int = 0,
    limit: int = 10,
    username: str = Depends(get_current_username),
    db: Session = Depends(get_db),
) -> List[models.FilmReview]:
    return crud.get_user_reviews(db, username=username, skip=skip, limit=limit)


@app.post(
    '/films/', response_model=schemas.Film, dependencies=[Depends(get_current_username)]
)
def create_film(film: schemas.FilmCreate, db: Session = Depends(get_db)) -> models.Film:
    try:
        return crud.create_film(db, film)
    except ValueError as e:
        logging.error(str(e))
        raise HTTPException(status_code=400, detail=str(e)) from e


@app.get(
    '/films/',
    response_model=List[schemas.Film],
    dependencies=[Depends(get_current_username)],
)
def read_films(
    skip: int = 0, limit: int = 10, db: Session = Depends(get_db)
) -> List[models.Film]:
    return crud.get_films(db, skip=skip, limit=limit)


@app.get(
    '/films/filter/substring/{substring}/',
    response_model=List[schemas.Film],
    dependencies=[Depends(get_current_username)],
)
def read_films_filtered_by_substring(
    substring: str, skip: int = 0, limit: int = 10, db: Session = Depends(get_db)
) -> List[models.Film]:
    return crud.get_films_filterby_substring(
        db, substring=substring, skip=skip, limit=limit
    )


@app.get(
    '/films/filter/release_year/{release_year}/',
    response_model=List[schemas.Film],
    dependencies=[Depends(get_current_username)],
)
def read_films_filtered_by_release_year(
    release_year: int, skip: int = 0, limit: int = 10, db: Session = Depends(get_db)
) -> List[models.Film]:
    return crud.get_films_filterby_release_year(
        db, release_year=release_year, skip=skip, limit=limit
    )


@app.get(
    '/films/filter/average/',
    response_model=List[schemas.Film],
    dependencies=[Depends(get_current_username)],
)
def read_films_filtered_by_average(
    skip: int = 0, limit: int = 100, db: Session = Depends(get_db)
) -> List[models.Film]:
    return crud.get_films_filterby_average(db, skip=skip, limit=limit)


@app.get(
    '/films/{film_name}/reviews/',
    response_model=List[schemas.Review],
    dependencies=[Depends(get_current_username)],
)
def read_film_reviews(
    film_name: str, skip: int = 0, limit: int = 10, db: Session = Depends(get_db)
) -> List[models.FilmReview]:
    return crud.get_film_reviews(db, film_name=film_name, skip=skip, limit=limit)


@app.get(
    '/films/{film_name}/extended/',
    response_model=schemas.FilmExtended,
    dependencies=[Depends(get_current_username)],
)
def read_film_extended_info(
    film_name: str, skip: int = 0, limit: int = 10, db: Session = Depends(get_db)
) -> schemas.FilmExtended:
    try:
        return crud.get_film_info_extended(
            db, film_name=film_name, skip=skip, limit=limit
        )
    except ValueError as e:
        logging.error(str(e))
        raise HTTPException(status_code=400, detail=str(e)) from e
