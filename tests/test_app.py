
import pytest

from app import create_app


@pytest.fixture
def client():
    app = create_app()
    app.config.update(TESTING=True)

    with app.test_client() as client:
        yield client


def test_homepage_loads(client):
    response = client.get("/")

    assert response.status_code == 200


def test_homepage_has_game_title(client):
    response = client.get("/")

    assert b"IRON" in response.data
    assert b"FLIGHT" in response.data


def test_mode_selection_exists(client):
    response = client.get("/")

    assert b"DRONE ASSAULT" in response.data
    assert b"FLIGHT ACADEMY" in response.data


def test_game_canvas_exists(client):
    response = client.get("/")

    assert b'id="game"' in response.data


def test_combat_script_exists(client):
    response = client.get("/static/js/game.js")

    assert response.status_code == 200
    assert b"spawnBoss" in response.data


def test_flight_script_exists(client):
    response = client.get("/static/js/flight.js")

    assert response.status_code == 200
    assert b"drawCheckpoint" in response.data


def test_stylesheet_exists(client):
    response = client.get("/static/css/style.css")

    assert response.status_code == 200
