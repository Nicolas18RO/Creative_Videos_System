"""API de listado de proyectos."""

from fastapi.testclient import TestClient

from aicos.api.main import app


def test_get_projects_returns_list() -> None:
    with TestClient(app, raise_server_exceptions=True) as client:
        r = client.get("/projects")
        assert r.status_code == 200
        assert isinstance(r.json(), list)
