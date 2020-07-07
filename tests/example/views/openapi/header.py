from indexpy.http import HTTPView
from indexpy.test import TestView
from pydantic import BaseModel


class Query(BaseModel):
    name: str


class HTTP(HTTPView):
    async def get(self, header: Query):
        return header.name

    async def catch_validation_error(self, e):
        """
        Used to handle request parsing errors
        """
        return self.request.headers.items(), 400


class Test(TestView):
    def test_get(self):
        resp = self.client.get(headers={"name": "123"})
        assert resp.json() == 123
        assert resp.status_code == 200
