from functools import lru_cache

import pytest
from fastapi import Depends, FastAPI
from starlette.testclient import TestClient


class Controller:
    def __init__(self, use_case):
        self._use_case = use_case

    async def execute(self):
        return await self._use_case.execute()


class UseCase:
    async def execute(self):
        return {"data": "use_case"}


class Registry:
    @classmethod
    def controller(cls):
        return _controller()

    @classmethod
    def use_case(cls):
        return _use_case()


@lru_cache
def _use_case():
    return UseCase()


@lru_cache
def _controller(uc=Depends(Registry.use_case)):
    return Controller(use_case=uc)

@pytest.fixture
def app():
    app = FastAPI()

    @app.get("/registry")
    async def ctl(c=Depends(Registry.controller)):
        return await c.execute()

    @app.get("/function")
    async def f(c=Depends(_controller)):
        return await c.execute()

    return app

@pytest.fixture
def client(app):
    return TestClient(app)


class TestRegistry:
    url = "/registry"

    def fake_controller(self):
        class FakeController:
            async def execute(self):
                return {"data": "fake_controller"}

        return FakeController()

    # fails with
    # async def execute(self):
    # >       return await self._use_case.execute()
    # E       AttributeError: 'Depends' object has no attribute 'execute'
    def test_can_with_controller_and_use_case(self, client):
        res = client.get(self.url)
        assert res.json() == {"data": "use_case"}

    # ok
    def test_can_override_controller(self, client, app):
        app.dependency_overrides[Registry.controller] = self.fake_controller
        res = client.get(self.url)
        assert res.json() == {"data": "fake_controller"}
        del app.dependency_overrides[Registry.controller]


class TestFunction:
    url = "/function"

    # ok
    def test_can_with_controller_and_use_case(self, client):
        res = client.get(self.url)
        assert res.json() == {"data": "use_case"}

