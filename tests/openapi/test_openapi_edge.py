from http import HTTPStatus
from typing import Any

import httpx
import pytest
from pydantic import BaseModel, create_model
from typing_extensions import Annotated

from kui.asgi import Body, JSONResponse, Kui, OpenAPI, Query, UploadFile


@pytest.mark.asyncio
async def test_openapi_security_schemes_in_constructor():
    openapi = OpenAPI(
        info={"title": "Test", "version": "0.1"},
        security_schemes={
            "CustomAuth": {"type": "apiKey", "name": "X-Key", "in": "header"}
        },
    )
    app = Kui()

    @app.router.http.get("/")
    async def homepage():
        return "ok"

    app.router <<= "/docs" // openapi.routes

    async with httpx.AsyncClient(
        transport=httpx.ASGITransport(app=app), base_url="http://testserver"
    ) as client:
        response = await client.get("/docs/json")

    assert "CustomAuth" in response.json()["components"]["securitySchemes"]


@pytest.mark.asyncio
async def test_openapi_tag_paths_mapping():
    openapi = OpenAPI(
        info={"title": "Test", "version": "0.1"},
        tags={"Users": {"description": "User ops", "paths": ["/users"]}},
    )
    app = Kui()

    @app.router.http.get("/users")
    async def list_users():
        return []

    app.router <<= "/docs" // openapi.routes

    async with httpx.AsyncClient(
        transport=httpx.ASGITransport(app=app), base_url="http://testserver"
    ) as client:
        response = await client.get("/docs/json")

    assert "Users" in response.json()["paths"]["/users"]["get"]["tags"]


@pytest.mark.asyncio
async def test_openapi_upload_file_forces_multipart():
    openapi = OpenAPI(info={"title": "Test", "version": "0.1"})
    app = Kui()

    @app.router.http.post("/upload")
    async def upload(file: Annotated[UploadFile, Body(...)]):
        return {"filename": file.filename}

    app.router <<= "/docs" // openapi.routes

    async with httpx.AsyncClient(
        transport=httpx.ASGITransport(app=app), base_url="http://testserver"
    ) as client:
        response = await client.get("/docs/json")

    request_body = response.json()["paths"]["/upload"]["post"]["requestBody"]
    assert list(request_body["content"]) == ["multipart/form-data"]


@pytest.mark.asyncio
async def test_openapi_multiple_response_status_codes():
    openapi = OpenAPI(info={"title": "Test", "version": "0.1"})
    app = Kui()

    class Item(BaseModel):
        name: str

    @app.router.http.get("/item")
    async def get_item() -> Annotated[
        Any, JSONResponse[200, {}, Item], JSONResponse[HTTPStatus.NOT_FOUND]
    ]:
        return Item(name="x")

    app.router <<= "/docs" // openapi.routes

    async with httpx.AsyncClient(
        transport=httpx.ASGITransport(app=app), base_url="http://testserver"
    ) as client:
        response = await client.get("/docs/json")

    responses = response.json()["paths"]["/item"]["get"]["responses"]
    assert "200" in responses
    assert "404" in responses


@pytest.mark.asyncio
async def test_openapi_root_path_schema_conflict_uses_root_prefix():
    openapi = OpenAPI(info={"title": "Test", "version": "0.1"})
    app = Kui()
    item_root = create_model("Item", name=(str, ...))
    item_users = create_model("Item", price=(int, ...))
    response_root = create_model("Response", item=(item_root, ...))
    response_users = create_model("Response", item=(item_users, ...))

    @app.router.http.get("/")
    async def get_root() -> Annotated[Any, JSONResponse[200, {}, response_root]]:
        return response_root(item=item_root(name="x"))

    @app.router.http.get("/users")
    async def get_users() -> Annotated[Any, JSONResponse[200, {}, response_users]]:
        return response_users(item=item_users(price=1))

    app.router <<= "/docs" // openapi.routes

    async with httpx.AsyncClient(
        transport=httpx.ASGITransport(app=app), base_url="http://testserver"
    ) as client:
        response = await client.get("/docs/json")

    spec = response.json()
    assert {"Root_Item", "Users_Item"} <= set(spec["components"]["schemas"])
    assert spec["paths"]["/"]["get"]["responses"]["200"]["content"][
        "application/json"
    ]["schema"]["properties"]["item"]["$ref"] == "#/components/schemas/Root_Item"
    assert spec["paths"]["/users"]["get"]["responses"]["200"]["content"][
        "application/json"
    ]["schema"]["properties"]["item"]["$ref"] == "#/components/schemas/Users_Item"


@pytest.mark.asyncio
async def test_openapi_non_conflicting_schema_passes_through():
    openapi = OpenAPI(info={"title": "Test", "version": "0.1"})
    app = Kui()

    metadata = create_model("Metadata", source=(str, ...))
    item_a = create_model("Item", name=(str, ...), meta=(metadata, ...))
    item_b = create_model("Item", price=(int, ...))
    other = create_model("Other", flag=(bool, ...))
    response_a = create_model("ResponseA", item=(item_a, ...))
    response_b = create_model("ResponseB", item=(item_b, ...))
    response_c = create_model("ResponseC", other=(other, ...))

    @app.router.http.get("/a")
    async def get_a() -> Annotated[Any, JSONResponse[200, {}, response_a]]:
        pass

    @app.router.http.get("/b")
    async def get_b() -> Annotated[Any, JSONResponse[200, {}, response_b]]:
        pass

    @app.router.http.get("/c")
    async def get_c() -> Annotated[Any, JSONResponse[200, {}, response_c]]:
        pass

    app.router <<= "/docs" // openapi.routes

    async with httpx.AsyncClient(
        transport=httpx.ASGITransport(app=app), base_url="http://testserver"
    ) as client:
        response = await client.get("/docs/json")

    spec = response.json()
    schemas = spec["components"]["schemas"]

    assert "Item" not in schemas
    assert {"A_Item", "B_Item", "Metadata", "Other"} <= set(schemas)
    assert schemas["A_Item"]["properties"]["meta"]["$ref"] == (
        "#/components/schemas/Metadata"
    )
    assert spec["paths"]["/c"]["get"]["responses"]["200"]["content"][
        "application/json"
    ]["schema"]["properties"]["other"]["$ref"] == "#/components/schemas/Other"


@pytest.mark.asyncio
async def test_openapi_same_content_schemas_grouped():
    openapi = OpenAPI(info={"title": "Test", "version": "0.1"})
    app = Kui()

    item_ab = create_model("Item", name=(str, ...))
    item_c = create_model("Item", price=(int, ...))
    response_a = create_model("ResponseA", item=(item_ab, ...))
    response_b = create_model("ResponseB", item=(item_ab, ...))
    response_c = create_model("ResponseC", item=(item_c, ...))

    @app.router.http.get("/a")
    async def get_a() -> Annotated[Any, JSONResponse[200, {}, response_a]]:
        pass

    @app.router.http.get("/b")
    async def get_b() -> Annotated[Any, JSONResponse[200, {}, response_b]]:
        pass

    @app.router.http.get("/c")
    async def get_c() -> Annotated[Any, JSONResponse[200, {}, response_c]]:
        pass

    app.router <<= "/docs" // openapi.routes

    async with httpx.AsyncClient(
        transport=httpx.ASGITransport(app=app), base_url="http://testserver"
    ) as client:
        response = await client.get("/docs/json")

    spec = response.json()
    schemas = spec["components"]["schemas"]
    ref_a = spec["paths"]["/a"]["get"]["responses"]["200"]["content"][
        "application/json"
    ]["schema"]["properties"]["item"]["$ref"]
    ref_b = spec["paths"]["/b"]["get"]["responses"]["200"]["content"][
        "application/json"
    ]["schema"]["properties"]["item"]["$ref"]
    ref_c = spec["paths"]["/c"]["get"]["responses"]["200"]["content"][
        "application/json"
    ]["schema"]["properties"]["item"]["$ref"]

    assert "Item" not in schemas
    assert {"A_Item", "C_Item"} <= set(schemas)
    assert ref_a == "#/components/schemas/A_Item"
    assert ref_b == ref_a
    assert ref_c == "#/components/schemas/C_Item"


@pytest.mark.asyncio
async def test_openapi_resolved_name_collision_adds_suffix():
    openapi = OpenAPI(info={"title": "Test", "version": "0.1"})
    app = Kui()

    existing_a_item = create_model("A_Item", existing=(bool, ...))
    existing_a_item_2 = create_model("A_Item_2", legacy=(str, ...))
    item_a = create_model("Item", name=(str, ...))
    item_b = create_model("Item", price=(int, ...))
    holder = create_model(
        "Holder", first=(existing_a_item, ...), second=(existing_a_item_2, ...)
    )
    response_a = create_model("ResponseA", item=(item_a, ...))
    response_b = create_model("ResponseB", item=(item_b, ...))
    response_c = create_model("ResponseC", holder=(holder, ...))

    @app.router.http.get("/a")
    async def get_a() -> Annotated[Any, JSONResponse[200, {}, response_a]]:
        pass

    @app.router.http.get("/b")
    async def get_b() -> Annotated[Any, JSONResponse[200, {}, response_b]]:
        pass

    @app.router.http.get("/c")
    async def get_c() -> Annotated[Any, JSONResponse[200, {}, response_c]]:
        pass

    app.router <<= "/docs" // openapi.routes

    async with httpx.AsyncClient(
        transport=httpx.ASGITransport(app=app), base_url="http://testserver"
    ) as client:
        response = await client.get("/docs/json")

    spec = response.json()
    schemas = spec["components"]["schemas"]

    assert {"A_Item", "A_Item_2", "A_Item_3", "B_Item"} <= set(schemas)
    assert spec["paths"]["/a"]["get"]["responses"]["200"]["content"][
        "application/json"
    ]["schema"]["properties"]["item"]["$ref"] == "#/components/schemas/A_Item_3"
    assert spec["paths"]["/b"]["get"]["responses"]["200"]["content"][
        "application/json"
    ]["schema"]["properties"]["item"]["$ref"] == "#/components/schemas/B_Item"


@pytest.mark.asyncio
async def test_openapi_response_merge_overlapping_status_codes():
    openapi = OpenAPI(info={"title": "Test", "version": "0.1"})
    app = Kui()

    class ErrorDetail(BaseModel):
        detail: str

    @app.router.http.get("/items")
    async def list_items(
        page: Annotated[int, Query(1)],
    ) -> Annotated[Any, JSONResponse[200], JSONResponse[422, {}, ErrorDetail]]:
        return []

    app.router <<= "/docs" // openapi.routes

    async with httpx.AsyncClient(
        transport=httpx.ASGITransport(app=app), base_url="http://testserver"
    ) as client:
        response = await client.get("/docs/json")

    responses = response.json()["paths"]["/items"]["get"]["responses"]
    assert "422" in responses
    assert "content" in responses["422"]
    assert "application/json" in responses["422"]["content"]


@pytest.mark.asyncio
async def test_openapi_response_no_overlap_updates():
    openapi = OpenAPI(info={"title": "Test", "version": "0.1"})
    app = Kui()

    class Item(BaseModel):
        name: str

    @app.router.http.get("/items")
    async def list_items(
        page: Annotated[int, Query(1)],
    ) -> Annotated[Any, JSONResponse[200, {}, Item]]:
        return []

    app.router <<= "/docs" // openapi.routes

    async with httpx.AsyncClient(
        transport=httpx.ASGITransport(app=app), base_url="http://testserver"
    ) as client:
        response = await client.get("/docs/json")

    responses = response.json()["paths"]["/items"]["get"]["responses"]
    assert "200" in responses
    assert "422" in responses
    assert "application/json" in responses["200"]["content"]


@pytest.mark.asyncio
async def test_openapi_response_merge_overlapping_without_content():
    openapi = OpenAPI(info={"title": "Test", "version": "0.1"})
    app = Kui()

    @app.router.http.get("/items")
    async def list_items(
        page: Annotated[int, Query(1)],
    ) -> Annotated[Any, JSONResponse[200], JSONResponse[422]]:
        return []

    app.router <<= "/docs" // openapi.routes

    async with httpx.AsyncClient(
        transport=httpx.ASGITransport(app=app), base_url="http://testserver"
    ) as client:
        response = await client.get("/docs/json")

    responses = response.json()["paths"]["/items"]["get"]["responses"]
    assert "422" in responses
    assert "content" in responses["422"]
    assert "application/json" in responses["422"]["content"]
