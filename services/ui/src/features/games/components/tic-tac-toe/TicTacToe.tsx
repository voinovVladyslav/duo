import useAuthStore from "@/features/auth/stores/auth"
import type { User } from "@/features/auth/types/user"
import type { GameMoveMessage } from "@/features/games/types/game"
import { TicTacToeStateSchema } from "@/features/games/types/tic-tac-toe"
import { GameHeader } from "../shared/GameHeader"
import { GameOverDialog } from "../shared/GameOverDialog"
import { GameBoard } from "./GameBoard"
import { getDialogTitle } from "../shared/gameOutcome"

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
        <div className="flex flex-col items-center gap-4 p-4">
            <GameOverDialog
                isOver={isOver}
                title={getDialogTitle(state, userId)}
            />

            <GameHeader
                opponentName={opponent ? opponent.email : "Opponent"}
                yourTurn={state.your_turn}
                isOver={isOver}
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
