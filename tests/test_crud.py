import hashlib

from app import crud, schemas
from tests.conftest import overriden_get_db


def test_get_user_in_db():
    login = 'user'
    password = 'topsecret'
    user_schema = schemas.UserCreate(login=login, password=password)
    db = next(overriden_get_db())
    crud.create_user(db, user_schema)

    hashed_password = hashlib.sha256(password.encode('utf-8')).hexdigest()

    user_in_db_schema = schemas.UserInDB(login='user', hashed_password=hashed_password)

    db = next(overriden_get_db())
    user = crud.get_user_in_db(db, user_in_db_schema)

    assert user is not None
    assert user.login == login
