from index.view import View
from index.background import after_response


@after_response
def only_print(message: str) -> None:
    print(message)


class HTTP(View):
    async def get(self):
        """
        welcome page
        """
        only_print("world")
        print("hello")
        return ""
