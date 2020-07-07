from tempfile import TemporaryFile

from indexpy.http import HTTPView
from indexpy.test import TestView
from indexpy.openapi import describe
from indexpy.openapi.types import File
from pydantic import BaseModel


class MultipartForm(BaseModel):
    file: File


class HTTP(HTTPView):
    @describe(
        200,
        """
        image/png:
            schema:
                type: string
                format: binary
        """,
    )
    @describe(
        403,
        """text/plain:
            schema:
                type: string
            example:
                pong
        """,
    )
    async def get(self):
        """
        get file
        """

    async def post(self, body: MultipartForm):
        """
        upload file
        """
        return body.file.filename


class Test(TestView):
    def test_post(self):
        f = TemporaryFile()
        resp = self.client.post(files={"file": f})
        assert resp.status_code == 200

    def test_post_error(self):
        resp = self.client.post(data={"file": "nothing"})
        assert resp.status_code == 400
