import functools
from abc import ABC, abstractmethod
from collections.abc import Callable
from typing import Any, Generic, Self, TypeVar

from opentelemetry import trace
from pydantic import BaseModel

TState = TypeVar('TState', bound=BaseModel)
TMove = TypeVar('TMove', bound=BaseModel)
TPlayerView = TypeVar('TPlayerView', bound=BaseModel)

_tracer = trace.get_tracer('duo.game.engine')

# decision/compute methods worth timing; wrapped automatically on each
# concrete engine so spans nest under the active gRPC request span
_TRACED_METHODS = (
    'is_move_possible',
    'make_move',
    'get_winner',
    'is_draw',
    'get_player_view',
    'get_current_player',
)


def _trace_engine_method(
    name: str, func: Callable[..., Any]
) -> Callable[..., Any]:
    @functools.wraps(func)
    def wrapper(self: Any, *args: Any, **kwargs: Any) -> Any:
        with _tracer.start_as_current_span(f'engine.{name}') as span:
            span.set_attribute('game.engine', type(self).__name__)
            return func(self, *args, **kwargs)

    return wrapper


class GameEngine(ABC, Generic[TState, TMove, TPlayerView]):
    state: TState

    def __init__(self, state: TState) -> None:
        self.state = state

    def __init_subclass__(cls, **kwargs: Any) -> None:
        super().__init_subclass__(**kwargs)
        for name in _TRACED_METHODS:
            impl = cls.__dict__.get(name)
            if callable(impl):
                setattr(cls, name, _trace_engine_method(name, impl))

    @abstractmethod
    def get_winner(self) -> int | None: ...

    @abstractmethod
    def is_draw(self) -> bool: ...

    def is_game_over(self) -> bool:
        return self.is_draw() or self.get_winner() is not None

    @abstractmethod
    def is_move_possible(self, move: TMove) -> bool: ...

    @abstractmethod
    def make_move(self, move: TMove) -> None: ...

    @abstractmethod
    def get_player_view(self, player_id: int) -> TPlayerView: ...

    @classmethod
    @abstractmethod
    def new_game(cls, p1: int, p2: int) -> Self: ...

    @classmethod
    @abstractmethod
    def load_game(cls, state: dict[str, Any]) -> Self: ...

    @classmethod
    @abstractmethod
    def load_move(cls, move: str) -> TMove: ...

    @abstractmethod
    def get_current_player(self) -> int: ...
