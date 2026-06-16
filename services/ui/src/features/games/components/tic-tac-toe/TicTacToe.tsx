import useAuthStore from "@/features/auth/stores/auth"
import type { User } from "@/features/auth/types/user"
import type { GameMoveMessage } from "@/features/games/types/game"
import { TicTacToeStateSchema } from "@/features/games/types/tic-tac-toe"
import { GameOverDialog } from "../shared/GameOverDialog"
import { GameStatus } from "../shared/GameStatus"
import { GameBoard } from "./GameBoard"
import { TicTacToeCell } from "./TicTacToeCell"
import { getDialogTitle, getStatusText } from "../shared/gameOutcome"
import { opponentSymbol } from "./utils"

interface Props {
    gameState: any
    sendMoveHandler: (message: GameMoveMessage) => void
    opponent: User | null
}

export function TicTacToe({ gameState, sendMoveHandler, opponent }: Props) {
    const userId = useAuthStore((state) => state.user?.id)
    const { data } = TicTacToeStateSchema.safeParse(gameState)
    if (data === undefined) {
        return <div>Failed to parse game state</div>
    }
    const state = data!
    const isOver = state.winner !== null || state.is_draw

    const handleClick = (i: number, j: number) => {
        sendMoveHandler({
            type: "game_move",
            body: { game_move: { coordinate: [i, j] } },
        })
    }

    return (
        <div className="flex flex-col items-center gap-6 p-8">
            <GameOverDialog
                isOver={isOver}
                title={getDialogTitle(state, userId)}
            />

            <div className="flex flex-col items-center gap-3">
                <h2 className="text-2xl font-bold tracking-tight">
                    Tic Tac Toe
                </h2>
                <div className="grid grid-cols-[1fr_auto_1fr] items-center gap-3">
                    <div
                        className={`flex items-center justify-end gap-1.5 transition-opacity ${!isOver && state.your_turn ? "opacity-100" : "opacity-40"}`}
                    >
                        <span className="text-sm font-medium text-foreground">
                            You
                        </span>
                        <TicTacToeCell value={state.your_symbol} />
                    </div>
                    <span className="text-xs font-semibold tracking-widest text-muted-foreground uppercase">
                        vs
                    </span>
                    <div
                        className={`flex min-w-0 items-center justify-start gap-1.5 transition-opacity ${!isOver && !state.your_turn ? "opacity-100" : "opacity-40"}`}
                    >
                        <TicTacToeCell
                            value={opponentSymbol(state.your_symbol)}
                        />
                        <span className="truncate text-sm font-medium text-foreground">
                            {opponent ? opponent.email : "Opponent"}
                        </span>
                    </div>
                </div>
            </div>

            <GameStatus
                isOver={isOver}
                yourTurn={state.your_turn}
                text={getStatusText(state, userId)}
            />

            <GameBoard
                board={state.board}
                yourTurn={state.your_turn}
                isOver={isOver}
                onCellClick={handleClick}
            />
        </div>
    )
}
