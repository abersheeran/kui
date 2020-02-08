from index.view import View
from index.openapi import models, describe


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
