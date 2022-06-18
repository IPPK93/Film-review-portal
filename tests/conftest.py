import logging
import os
from pathlib import Path

import pytest
from dotenv import load_dotenv
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.fastapi_app import app, get_current_username, get_db
from app.models import Base

users = [
    {'login': 'test_user', 'password': 'test_password'},
    {'login': 'not_test_user', 'password': 'test_password'},
    {'login': 'p_user', 'password': 'test_password'},
]

films = [
    {'name': 'test_film', 'release_year': 2019},
    {'name': 'testie__film2', 'release_year': 2019},
    {'name': 't_est_film3', 'release_year': 2016},
    {'name': 'te__st_film4', 'release_year': 2012},
    {'name': 'telsfilm5', 'release_year': 2022},
]

reviews = [
    {'film_name': 'test_film', 'review': 'Good stuff', 'mark': 2},
    {'film_name': 'testie__film2', 'review': 'Good stuff?', 'mark': 7},
    {'film_name': 't_est_film3', 'review': 'Good stuff!', 'mark': 5},
    {'film_name': 'te__st_film4', 'review': 'GOOD stuff', 'mark': 10},
]


def init_db():
    load_dotenv()

    SQLALCHEMY_DATABASE_URL_TESTING = os.environ['SQLALCHEMY_DATABASE_URL_TESTING']

    engine_ = create_engine(
        SQLALCHEMY_DATABASE_URL_TESTING, connect_args={'check_same_thread': False}
    )
    TestingSession = sessionmaker(autocommit=False, autoflush=False, bind=engine_)

    return TestingSession, engine_


TestingSessionLocal, engine = init_db()


def overriden_get_db():
    db = TestingSessionLocal()
    try:
        yield db
    finally:
        db.close()


@pytest.fixture(autouse=True)
def setup():
    load_dotenv()

    log_file = os.environ.get('TEST_LOG_FILE')
    logging.basicConfig(filename=log_file, level=logging.INFO, force=True)
    Base.metadata.create_all(bind=engine)

    yield

    Base.metadata.drop_all(bind=engine)


@pytest.fixture(autouse=True, scope='session')
def teardown_session():
    yield
    db_filename = os.environ.get('TEST_DB_FILENAME')
    if db_filename is not None:
        Path(db_filename).unlink(missing_ok=True)


@pytest.fixture(name='client')
def client_() -> TestClient:
    app.dependency_overrides[get_db] = overriden_get_db
    app.dependency_overrides[get_current_username] = lambda: 'test_user'
    return TestClient(app)


@pytest.fixture(name='client_w_user')
def client_w_user_(client: TestClient) -> TestClient:
    client.post('/users/', json={'login': 'test_user', 'password': 'test_password'})
    return client


@pytest.fixture(name='client_w_film')
def client_w_film_(client_w_user: TestClient) -> TestClient:
    client_w_user.post('/films/', json={'name': 'test_film', 'release_year': 2019})
    return client_w_user


@pytest.fixture(name='client_w_review')
def client_w_review_(client_w_film: TestClient) -> TestClient:
    client_w_film.post(
        '/users/me/reviews/',
        json={'film_name': 'test_film', 'review': 'Good stuff', 'mark': 8},
    )
    return client_w_film


@pytest.fixture(name='client_w_many_reviews')
def client_w_many_reviews_(client: TestClient) -> TestClient:
    for user in users:
        client.post('/users/', json=user)
    for film in films:
        client.post('/films/', json=film)
    for i, user in enumerate(users):
        for j, review in enumerate(reviews):
            user_review = review.copy()
            if isinstance(user_review['mark'], int):
                user_review['mark'] = (user_review['mark'] + i + j) % 10
            app.dependency_overrides[get_current_username] = lambda u=user: u['login']
            client.post('/users/me/reviews/', json=user_review)
    app.dependency_overrides[get_current_username] = lambda: 'test_user'
    return client
