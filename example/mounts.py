from index import app
from index.openapi.application import OpenAPI

app.mount("openapi", OpenAPI)

print("hello", flush=True)
