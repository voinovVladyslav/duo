import { z } from "zod"

type GameType = "tic_tac_toe" | "battleships"

type GameResult = "tbd" | "draw" | "p1_won" | "p2_won"

type GameStatus = "in_queue" | "in_progress" | "abandoned" | "finished"

type Game = {
    id: number
    type: GameType
    result: GameResult
    status: GameStatus
    player1: number
    player2: number | null
    current_player: number
    turn_number: number
    created_at: string
    updated_at: string
}

interface GameCreate {
    type: GameType
}

export type { Game, GameType, GameResult, GameStatus, GameCreate }

export const TokenMessageScheme = z.object({
    type: z.literal("token"),
    body: z.object({ token: z.string() }),
})
export const AuthenticatedMessageScheme = z.object({
    type: z.literal("authenticated"),
    body: z.object({ success: z.boolean(), message: z.string() }),
})
export const GameMoveMessageScheme = z.object({
    type: z.literal("game_move"),
    body: z.object({ game_move: z.record(z.any(), z.any()) }),
})
export const GameStateMessageScheme = z.object({
    type: z.literal("game_state"),
    body: z.object({ game_state: z.unknown() }),
})
export const GameCreatedMessageScheme = z.object({
    type: z.literal("game_created"),
    body: z.object({ message: z.string() }),
})
export const ConnectedMessageScheme = z.object({
    type: z.literal("connected"),
    body: z.object({ message: z.string() }),
})
export const DisconnectedMessageScheme = z.object({
    type: z.literal("disconnected"),
    body: z.object({ message: z.string() }),
})
export const InvalidMoveMessageScheme = z.object({
    type: z.literal("invalid_move"),
    body: z.object({ message: z.string() }),
})

export const GameMessageScheme = z.discriminatedUnion("type", [
    TokenMessageScheme,
    AuthenticatedMessageScheme,
    GameMoveMessageScheme,
    GameStateMessageScheme,
    GameCreatedMessageScheme,
    ConnectedMessageScheme,
    DisconnectedMessageScheme,
    InvalidMoveMessageScheme,
])

export type TokenMessage = z.infer<typeof TokenMessageScheme>
export type AuthenticatedMessage = z.infer<typeof AuthenticatedMessageScheme>
export type GameMoveMessage = z.infer<typeof GameMoveMessageScheme>
export type GameStateMessage = z.infer<typeof GameStateMessageScheme>
export type GameCreatedMessage = z.infer<typeof GameCreatedMessageScheme>
export type ConnectedMessage = z.infer<typeof ConnectedMessageScheme>
export type DisconnectedMessage = z.infer<typeof DisconnectedMessageScheme>
export type InvalidMoveMessage = z.infer<typeof InvalidMoveMessageScheme>
export type GameMessage = z.infer<typeof GameMessageScheme>
