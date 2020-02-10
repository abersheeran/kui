from tempfile import TemporaryFile

from indexpy.view import View
from indexpy.test import TestView
from indexpy.openapi import models, describe
from indexpy.openapi.types import File


class MultipartForm(models.Model):
    file: File


class HTTP(View):
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
        f.name = "temporary"

        resp = self.client.post(files={"file": f})
        assert resp.status_code == 200
        assert resp.text == "temporary"
