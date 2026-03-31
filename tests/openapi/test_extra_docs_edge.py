from kui.asgi import HttpView
from kui.openapi import describe_extra_docs


def test_describe_extra_docs_on_class_view():
    class MyView(HttpView):
        async def get(self):
            return "ok"

        async def post(self):
            return "ok"

    MyView.__methods__ = ["GET", "POST"]

    describe_extra_docs(MyView, {"deprecated": True})

    assert MyView.get.__docs_extra__["deprecated"] is True
    assert MyView.post.__docs_extra__["deprecated"] is True


def test_describe_extra_docs_on_function():
    async def handler():
        return "ok"

    describe_extra_docs(handler, {"deprecated": True})

    assert handler.__docs_extra__["deprecated"] is True


def test_describe_extra_docs_merges():
    async def handler():
        return "ok"

    describe_extra_docs(handler, {"tags": ["a"]})
    describe_extra_docs(handler, {"tags": ["b"]})

    assert handler.__docs_extra__["tags"] == ["a", "b"]
