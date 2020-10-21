from indexpy.openapi.functions import describe_response, describe_responses


def test_describe_response():
    class HTTP:
        @describe_response(200, "ok")
        @describe_response(400, "bad request")
        async def get(self):
            pass

    assert HTTP.get.__responses__ == {
        200: {"description": "ok"},
        400: {"description": "bad request"},
    }


def test_describe_responses():
    class HTTP:
        @describe_responses(
            {
                200: {"description": "ok"},
                400: {"description": "bad request"},
            }
        )
        async def get(self):
            pass

    assert HTTP.get.__responses__ == {
        200: {"description": "ok"},
        400: {"description": "bad request"},
    }
