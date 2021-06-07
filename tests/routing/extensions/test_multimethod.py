from indexpy import HttpRoute
from indexpy.routing.extensions import MultimethodRoutes as Routes


def test_mulitmethodroutes():
    routes = Routes()
    routes << Routes(
        HttpRoute("/login", test_mulitmethodroutes),
        HttpRoute("/register", test_mulitmethodroutes),
    )
    routes == Routes(
        HttpRoute("/login", test_mulitmethodroutes),
        HttpRoute("/register", test_mulitmethodroutes),
    )

    (
        routes
        << Routes(
            HttpRoute("/login", test_mulitmethodroutes),
            HttpRoute("/register", test_mulitmethodroutes),
        )
    ) == (
        Routes(
            HttpRoute("/login", test_mulitmethodroutes),
            HttpRoute("/register", test_mulitmethodroutes),
        )
        + Routes(
            HttpRoute("/login", test_mulitmethodroutes),
            HttpRoute("/register", test_mulitmethodroutes),
        )
    )
