from enum import Enum

from generated import game_pb2


class Type(str, Enum):
    TIC_TAC_TOE = 'tic_tac_toe'
    BATTLESHIPS = 'battleships'


class Result(str, Enum):
    TBD = 'tbd'
    DRAW = 'draw'
    P1_WON = 'p1_won'
    P2_WON = 'p2_won'


class Status(str, Enum):
    IN_QUEUE = 'in_queue'
    IN_PROGRESS = 'in_progress'
    ABANDONED = 'abandoned'
    FINISHED = 'finished'


TYPE_TO_PROTO_MAP: dict[Type, game_pb2.GameType.ValueType] = {
    Type.TIC_TAC_TOE: game_pb2.TIC_TAC_TOE,
    Type.BATTLESHIPS: game_pb2.BATTLESHIPS,
}

RESULT_TO_PROTO_MAP: dict[Result, game_pb2.GameResult.ValueType] = {
    Result.TBD: game_pb2.TBD,
    Result.DRAW: game_pb2.DRAW,
    Result.P1_WON: game_pb2.P1_WON,
    Result.P2_WON: game_pb2.P2_WON,
}

STATUS_TO_PROTO_MAP: dict[Status, game_pb2.GameStatus.ValueType] = {
    Status.IN_QUEUE: game_pb2.IN_QUEUE,
    Status.IN_PROGRESS: game_pb2.IN_PROGRESS,
    Status.ABANDONED: game_pb2.ABANDONED,
    Status.FINISHED: game_pb2.FINISHED,
}

TYPE_FROM_PROTO_MAP: dict[game_pb2.GameType.ValueType, Type] = {
    game_pb2.TIC_TAC_TOE: Type.TIC_TAC_TOE,
    game_pb2.BATTLESHIPS: Type.BATTLESHIPS,
}

RESULT_FROM_PROTO_MAP: dict[game_pb2.GameResult.ValueType, Result] = {
    game_pb2.TBD: Result.TBD,
    game_pb2.DRAW: Result.DRAW,
    game_pb2.P1_WON: Result.P1_WON,
    game_pb2.P2_WON: Result.P2_WON,
}

STATUS_FROM_PROTO_MAP: dict[game_pb2.GameStatus.ValueType, Status] = {
    game_pb2.IN_QUEUE: Status.IN_QUEUE,
    game_pb2.IN_PROGRESS: Status.IN_PROGRESS,
    game_pb2.ABANDONED: Status.ABANDONED,
    game_pb2.FINISHED: Status.FINISHED,
}
