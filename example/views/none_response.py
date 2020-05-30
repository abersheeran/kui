from indexpy.http import HTTPView
from indexpy.test import TestView


class HTTP(HTTPView):
    async def get(self):
        pass


class Test(TestView):
    def test_none(self):
        import pytest

        with pytest.raises(
            TypeError,
            match="Get 'None'. Maybe you need to add a return statement to the function.",
        ):
            self.client.get()
