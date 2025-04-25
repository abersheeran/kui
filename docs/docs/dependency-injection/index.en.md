Kuí has dependency injection functionality and is capable of automatically generating corresponding OpenAPI documentation.

Functions outside of HTTP handlers can use the `@auto_params` decorator for automatic dependency injection. However, note that the function decorated with `@auto_params` must be used in an environment that contains the `request` context. Otherwise, dependency injection will throw an error.
