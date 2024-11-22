from typing import Any, Dict, Generic, Optional, TypeVar, Union

T = TypeVar("T")
E = TypeVar("E")


class Result(Generic[T, E]):
    def __init__(self, value: Union[T, None] = None, error: Union[E, None] = None):
        self.value = value
        self.error = error
        self.metadata: Dict[str, Any] = {}

    def is_ok(self) -> bool:
        return self.error is None

    def is_error(self) -> bool:
        return self.error is not None

    def unwrap(self) -> T:
        if self.is_error():
            raise ValueError("Called unwrap on an error result")
        return self.value

    def unwrap_error(self) -> E:
        if self.is_ok():
            raise ValueError("Called unwrap_error on a success result")
        return self.error

    def with_metadata(self, key: str, value: Any) -> "Result[T, E]":
        self.metadata[key] = value
        return self

    def get_metadata(self, key: str, default: Optional[Any] = None) -> Any:
        return self.metadata.get(key, default)
