"""
OpenAPI specification 3.0.3

https://github.com/OAI/OpenAPI-Specification/blob/main/versions/3.0.3.md
"""
from __future__ import annotations

from typing import Any, Dict, List, Union

from typing_extensions import Literal, TypedDict


class _OpenAPIRequired(TypedDict):
    openapi: str
    info: Info
    paths: Paths


class OpenAPI(_OpenAPIRequired, total=False):
    servers: List[Server]
    components: Components
    security: List[SecurityRequirement]
    tags: List[Tag]
    externalDocs: ExternalDocumentation


class _InfoRequired(TypedDict):
    title: str
    version: str


class Info(_InfoRequired, total=False):
    description: str
    terms_of_service: str
    contact: Contact
    license: License


class Contact(TypedDict, total=False):
    name: str
    url: str
    email: str


class _LicenseRequired(TypedDict):
    name: str


class License(_LicenseRequired, total=False):
    url: str


class _ServerRequired(TypedDict):
    url: str


class Server(_ServerRequired, total=False):
    description: str
    variables: Dict[str, ServerVariable]


class _ServerVariableRequired(TypedDict):
    default: str


class ServerVariable(_ServerVariableRequired, total=False):
    enum: List[str]
    description: str


class Components(TypedDict, total=False):
    schemas: Dict[str, Schema | Reference]
    responses: Dict[str, Response | Reference]
    parameters: Dict[str, Parameter | Reference]
    examples: Dict[str, Example | Reference]
    requestBodies: Dict[str, RequestBody | Reference]
    headers: Dict[str, Header | Reference]
    securitySchemes: Dict[str, SecurityScheme | Reference]
    links: Dict[str, Link | Reference]
    callbacks: Dict[str, Callback | Reference]


Paths = Dict[str, "PathItem"]

_PathRef = TypedDict("_PathRef", {"$ref": str}, total=False)


class PathItem(_PathRef, total=False):
    summary: str
    description: str
    get: Operation
    put: Operation
    post: Operation
    delete: Operation
    options: Operation
    head: Operation
    patch: Operation
    trace: Operation
    servers: List[Server]
    parameters: List[Parameter | Reference]


class _OperationRequired(TypedDict):
    responses: Responses


class Operation(_OperationRequired, total=False):
    tags: List[str]
    summary: str
    description: str
    externalDocs: ExternalDocumentation
    operationId: str
    parameters: List[Parameter | Reference]
    requestBody: RequestBody | Reference
    callbacks: Dict[str, Callback | Reference]
    deprecated: bool
    security: List[SecurityRequirement]
    servers: List[Server]


class _ExternalDocumentationRequired(TypedDict):
    url: str


class ExternalDocumentation(_ExternalDocumentationRequired, total=False):
    description: str


# Beacuse "in" is a key word in python
_ParameterRequired = TypedDict("_ParameterRequired", {"name": str, "in": str})


class _ParameterOptional(TypedDict, total=False):
    description: str
    required: bool
    deprecated: bool
    allowEmptyValue: bool

    style: str
    explode: bool
    allowReserved: bool
    schema: Schema | Reference
    example: Any
    examples: Dict[str, Example | Reference]

    content: Dict[str, MediaType]


class Parameter(_ParameterRequired, _ParameterOptional):
    pass


class _RequestBodyRequired(TypedDict):
    content: Dict[str, MediaType]


class RequestBody(_RequestBodyRequired, total=False):
    description: str
    required: bool


class MediaType(TypedDict, total=False):
    schema: Schema | Reference
    example: Any
    examples: Dict[str, Example | Reference]
    encoding: Dict[str, Encoding]


class Encoding(TypedDict, total=False):
    contentType: str
    headers: Dict[str, Header | Reference]
    style: str
    explode: bool
    allowReserved: bool


Responses = Dict[str, "Response"]


class _ResponseRequired(TypedDict):
    description: str


class Response(_ResponseRequired, total=False):
    headers: Dict[str, Header | Reference]
    content: Dict[str, MediaType]
    links: Dict[str, Link | Reference]


Callback = Dict[str, "PathItem"]


class Example(TypedDict, total=False):
    summary: str
    description: str
    value: Any
    externalValue: str


class Link(TypedDict, total=False):
    operationRef: str
    operationId: str
    parameters: Dict[str, Any]
    requestBody: Any
    description: str
    server: Server


class Header(TypedDict, total=False):
    description: str
    required: bool
    deprecated: bool
    allowEmptyValue: bool

    style: str
    explode: bool
    allowReserved: bool
    schema: Schema | Reference
    example: Any
    examples: Dict[str, Example | Reference]

    content: Dict[str, MediaType]


class _TagRequired(TypedDict):
    name: str


class Tag(_TagRequired, total=False):
    description: str
    external_docs: ExternalDocumentation


Reference = TypedDict("Reference", {"$ref": str})

_Schema = TypedDict("_Schema", {"not": Union[Reference, "Schema"]}, total=False)


class Schema(_Schema, total=False):
    title: str
    multipleOf: float
    maximum: float
    exclusiveMaximum: bool
    minimum: float
    exclusiveMinimum: bool
    maxLength: int
    minLength: int
    pattern: str
    maxItems: int
    minItems: int
    uniqueItems: bool
    maxProperties: int
    minProperties: int
    required: List[str]
    enum: List[Any]
    type: str
    allOf: List[Reference | Schema]
    oneOf: List[Reference | Schema]
    anyOf: List[Reference | Schema]
    items: Reference | Schema
    properties: Dict[str, Reference | Schema]
    additionalProperties: bool | Reference | Schema
    description: str
    format: str
    default: Any
    nullable: bool
    discriminator: Discriminator
    readOnly: bool
    writeOnly: bool
    xml: XML
    externalDocs: ExternalDocumentation
    example: Any
    deprecated: bool


class _DiscriminatorRequired(TypedDict):
    propertyName: str


class Discriminator(_DiscriminatorRequired, total=False):
    mapping: Dict[str, str]


class XML(TypedDict, total=False):
    name: str
    namespace: str
    prefix: str
    attribute: str
    wrapped: bool


# Beacuse "in" is a key word in python
_ApiKeyScheme = TypedDict(
    "_ApiKeyScheme",
    {
        "type": Literal["apiKey"],
        "name": str,
        "in": Literal["query", "header", "cookie"],
    },
)


class _SecuritySchemeOptional(TypedDict, total=False):
    description: str


class ApiKeyScheme(_ApiKeyScheme, _SecuritySchemeOptional):
    pass


class HttpScheme(_SecuritySchemeOptional):
    type: Literal["http"]
    scheme: str


class _HttpBearerSchemeOptional(TypedDict, total=False):
    bearerFormat: str


class HttpBearerScheme(_SecuritySchemeOptional, _HttpBearerSchemeOptional):
    type: Literal["http"]
    scheme: Literal["bearer"]


class OAuth2Scheme(_SecuritySchemeOptional):
    type: Literal["oauth2"]
    flows: OAuthFlows


class OpenIdConnectScheme(_SecuritySchemeOptional):
    type: Literal["openIdConnect"]
    openIdConnectUrl: str


SecurityScheme = Union[
    ApiKeyScheme, HttpScheme, HttpBearerScheme, OAuth2Scheme, OpenIdConnectScheme
]


class OAuthFlows(TypedDict, total=False):
    implicit: OAuthFlowImplicit
    password: OAuthFlowPassword
    clientCredentials: OAuthFlowClientCredentials
    authorizationCode: OAuthFlowAuthorizationCode


class _OAuthFlowBase(TypedDict, total=False):
    refreshUrl: str


class OAuthFlowBase(_OAuthFlowBase):
    scopes: Dict[str, str]


class OAuthFlowImplicit(OAuthFlowBase):
    authorizationUrl: str


class OAuthFlowPassword(OAuthFlowBase):
    tokenUrl: str


class OAuthFlowClientCredentials(OAuthFlowBase):
    tokenUrl: str


class OAuthFlowAuthorizationCode(OAuthFlowBase):
    authorizationUrl: str
    tokenUrl: str


SecurityRequirement = Dict[str, List[str]]
