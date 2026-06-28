from __future__ import annotations

from dataclasses import dataclass
from functools import wraps
from inspect import Signature, signature
from types import SimpleNamespace
from typing import Any, Callable, get_type_hints

from pydantic import BaseModel


class Request:
    def __init__(self, app: "FastAPI") -> None:
        self.app = app


@dataclass
class _Route:
    method: str
    path: str
    handler: Callable[..., Any]
    response_model: type[BaseModel] | None = None


class FastAPI:
    def __init__(self, *, title: str = "FastAPI", version: str = "0.1.0") -> None:
        self.title = title
        self.version = version
        self.state = SimpleNamespace()
        self._routes: list[_Route] = []

    def get(self, path: str, response_model: type[BaseModel] | None = None):
        return self._route_decorator("GET", path, response_model=response_model)

    def post(self, path: str, response_model: type[BaseModel] | None = None):
        return self._route_decorator("POST", path, response_model=response_model)

    def _route_decorator(self, method: str, path: str, *, response_model: type[BaseModel] | None):
        def decorator(func: Callable[..., Any]) -> Callable[..., Any]:
            self._routes.append(_Route(method=method, path=path, handler=func, response_model=response_model))

            @wraps(func)
            def wrapped(*args: Any, **kwargs: Any) -> Any:
                return func(*args, **kwargs)

            return wrapped

        return decorator

    def _resolve_route(self, method: str, path: str) -> _Route:
        for route in self._routes:
            if route.method == method and route.path == path:
                return route
        raise KeyError(f"No route registered for {method} {path}")


def _coerce_value(annotation: Any, value: Any, app: FastAPI) -> Any:
    if annotation is Request:
        return Request(app)
    if isinstance(annotation, type) and issubclass(annotation, BaseModel):
        return annotation.model_validate(value)
    return value


def _serialize_value(value: Any) -> Any:
    if isinstance(value, BaseModel):
        return value.model_dump()
    return value


class _Response:
    def __init__(self, status_code: int, payload: Any) -> None:
        self.status_code = status_code
        self._payload = payload

    def json(self) -> Any:
        return self._payload


class TestClient:
    def __init__(self, app: FastAPI) -> None:
        self.app = app

    def get(self, path: str) -> _Response:
        route = self.app._resolve_route("GET", path)
        payload = self._invoke(route, None)
        return _Response(200, payload)

    def post(self, path: str, json: dict[str, Any] | None = None) -> _Response:
        route = self.app._resolve_route("POST", path)
        payload = self._invoke(route, json or {})
        return _Response(200, payload)

    def _invoke(self, route: _Route, body: dict[str, Any] | None) -> Any:
        bound_arguments = []
        sig: Signature = signature(route.handler)
        hints = get_type_hints(route.handler)
        for parameter in sig.parameters.values():
            annotation = hints.get(parameter.name, parameter.annotation)
            if body is None:
                bound_arguments.append(_coerce_value(annotation, None, self.app))
                continue
            if annotation is Request:
                bound_arguments.append(Request(self.app))
                continue
            if parameter.name in body:
                bound_arguments.append(body[parameter.name])
                continue
            if len(sig.parameters) == 1:
                bound_arguments.append(_coerce_value(annotation, body, self.app))
                continue
            bound_arguments.append(_coerce_value(annotation, body, self.app))

        result = route.handler(*bound_arguments)
        return _serialize_value(result)


__all__ = ["FastAPI", "Request", "TestClient"]
