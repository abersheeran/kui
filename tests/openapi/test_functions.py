from indexpy.openapi.functions import describe_response


def test_describe():
    class HTTP:
        @describe_response(200, "ok")
        @describe_response(400, "bad request")
        async def get(self):
            pass

    assert HTTP.get.__responses__[200]["description"] == "ok"
    assert HTTP.get.__responses__[400]["description"] == "bad request"
