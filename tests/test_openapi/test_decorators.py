from index.openapi.decorators import bindresponse


def test_bindresponse():
    class HTTP:
        @bindresponse(200, "ok")
        @bindresponse(400, "bad request")
        async def get(self):
            pass

    assert HTTP.get.__resps__[200] == "ok"
    assert HTTP.get.__resps__[400] == "bad request"
