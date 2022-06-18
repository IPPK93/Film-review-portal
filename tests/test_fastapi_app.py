import pytest
from fastapi.testclient import TestClient

user_body = {'login': 'test_user', 'password': 'test_password'}

film_body = {'name': 'test_film', 'release_year': 2019}

review_body = {'film_name': 'test_film', 'review': 'Good stuff', 'mark': 8}


def test_create_user(client: TestClient):
    response = client.post('/users/', json=user_body)

    assert response.status_code == 200
    assert response.json() == {'login': 'test_user', 'film_reviews': []}

    response_get = client.get('/users/?skip=0&limit=10')
    assert response_get.status_code == 200
    assert response_get.json() == [response.json()]


def test_create_user_httpexception(client_w_user: TestClient):
    response = client_w_user.post('/users/', json=user_body)

    assert response.status_code == 400
    assert (
        response.json()['detail']
        == 'User with login test_user already exists in database'
    )


def test_create_film(client: TestClient):
    response = client.post('/films/', json=film_body)

    assert response.status_code == 200
    assert response.json() == film_body

    response_get = client.get('/films/')

    assert response_get.status_code == 200
    assert response_get.json() == [response.json()]


def test_create_film_httpexception(client_w_film: TestClient):
    response = client_w_film.post('/films/', json=film_body)

    assert response.status_code == 400
    assert (
        response.json()['detail']
        == 'Film with name test_film already exists in database'
    )


def test_create_user_review(client_w_film: TestClient):
    response = client_w_film.post('/users/me/reviews/', json=review_body)

    assert response.status_code == 200
    assert response.json() == dict(**review_body, login='test_user')

    response_get = client_w_film.get('/users/me/reviews/')

    assert response_get.status_code == 200
    assert response_get.json() == [response.json()]


def test_create_user_review_httpexception_nonexistent(client_w_film: TestClient):
    nonexistent_film_body = {
        'film_name': 'TotallyNonExistentFilm',
        'review': 'Good stuff',
        'mark': 8,
    }
    response = client_w_film.post('users/me/reviews/', json=nonexistent_film_body)

    assert response.status_code == 400
    assert (
        response.json()['detail']
        == 'Film with name TotallyNonExistentFilm does not exist in database'
    )


def test_create_user_review_httpexception_reviewed(client_w_review: TestClient):
    response = client_w_review.post('users/me/reviews/', json=review_body)

    assert response.status_code == 400
    assert (
        response.json()['detail']
        == 'Film with name test_film have already been reviewed by user test_user'
    )


def test_read_user_review(client_w_review: TestClient):
    response = client_w_review.get('/users/me/reviews/test_film/')

    assert response.status_code == 200
    assert response.json() == dict(**review_body, login='test_user')


def test_read_user_review_valueerror(client_w_review: TestClient):
    response = client_w_review.get('/users/me/reviews/test_film2/')

    assert response.status_code == 400
    assert (
        response.json()['detail']
        == 'Film with name test_film2 does not exist in database'
    )


@pytest.mark.parametrize(
    ('substring', 'expected'),
    [
        (
            'est',
            [
                {'name': 'test_film', 'release_year': 2019},
                {'name': 'testie__film2', 'release_year': 2019},
                {'name': 't_est_film3', 'release_year': 2016},
            ],
        ),
        ('5', [{'name': 'telsfilm5', 'release_year': 2022}]),
        (
            'te',
            [
                {'name': 'test_film', 'release_year': 2019},
                {'name': 'testie__film2', 'release_year': 2019},
                {'name': 'te__st_film4', 'release_year': 2012},
                {'name': 'telsfilm5', 'release_year': 2022},
            ],
        ),
    ],
)
def test_read_films_filtered_by_substring(client_w_many_reviews, substring, expected):
    response = client_w_many_reviews.get(f'/films/filter/substring/{substring}/')

    assert response.status_code == 200
    assert response.json() == expected


@pytest.mark.parametrize(
    ('release_year', 'expected'),
    [
        (
            2019,
            [
                {'name': 'test_film', 'release_year': 2019},
                {'name': 'testie__film2', 'release_year': 2019},
            ],
        ),
        (2022, [{'name': 'telsfilm5', 'release_year': 2022}]),
    ],
)
def test_read_films_filtered_by_release_year(
    client_w_many_reviews, release_year, expected
):
    response = client_w_many_reviews.get(f'/films/filter/release_year/{release_year}')

    assert response.status_code == 200
    assert response.json() == expected


def test_read_films_filtered_by_average(client_w_many_reviews):
    expected = [
        {'name': 't_est_film3', 'release_year': 2016},
        {'name': 'testie__film2', 'release_year': 2019},
        {'name': 'te__st_film4', 'release_year': 2012},
        {'name': 'test_film', 'release_year': 2019},
    ]
    response = client_w_many_reviews.get('/films/filter/average/')

    assert response.json() == expected


@pytest.mark.parametrize(
    ('film_name', 'expected'),
    [
        (
            't_est_film3',
            {
                'name': 't_est_film3',
                'release_year': 2016,
                'average_mark': 8.0,
                'number_of_marks': 3,
                'number_of_reviews': 3,
                'reviews': [
                    {
                        'film_name': 't_est_film3',
                        'review': 'Good stuff!',
                        'mark': 7,
                        'login': 'test_user',
                    },
                    {
                        'film_name': 't_est_film3',
                        'review': 'Good stuff!',
                        'mark': 8,
                        'login': 'not_test_user',
                    },
                    {
                        'film_name': 't_est_film3',
                        'review': 'Good stuff!',
                        'mark': 9,
                        'login': 'p_user',
                    },
                ],
            },
        ),
        (
            'telsfilm5',
            {
                'name': 'telsfilm5',
                'release_year': 2022,
                'average_mark': None,
                'number_of_marks': 0,
                'number_of_reviews': 0,
                'reviews': [],
            },
        ),
    ],
)
def test_read_film_extended_info(
    client_w_many_reviews: TestClient, film_name, expected
):
    response = client_w_many_reviews.get(f'/films/{film_name}/extended/')

    assert response.json() == expected


def test_read_film_extended_info_valueerror(client: TestClient):
    response = client.get('/films/nonexistent_film/extended')

    assert response.status_code == 400
    assert (
        response.json()['detail']
        == 'Film with name nonexistent_film does not exist in database'
    )


def test_read_film_reviews(client_w_review: TestClient):
    expected = [
        {
            'film_name': 'test_film',
            'review': 'Good stuff',
            'mark': 8,
            'login': 'test_user',
        }
    ]
    response = client_w_review.get('/films/test_film/reviews/')

    assert response.status_code == 200
    assert response.json() == expected
