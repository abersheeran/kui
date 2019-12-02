from index.openapi.functions import describe


def test_describe():
    class HTTP:
        @describe(200, "ok")
        @describe(400, "bad request")
        async def get(self):
            pass

    assert HTTP.get.__resps__[200]["model"] == "ok"
    assert HTTP.get.__resps__[400]["model"] == "bad request"
