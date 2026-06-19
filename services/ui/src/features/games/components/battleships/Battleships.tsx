import useAuthStore from "@/features/auth/stores/auth"
import type { User } from "@/features/auth/types/user"
import { BattleshipsStateSchema } from "@/features/games/types/battleships"
import type { GameMoveMessage } from "@/features/games/types/game"
import { GameHeader } from "../shared/GameHeader"
import { GameOverDialog } from "../shared/GameOverDialog"
import { GameBoard } from "./GameBoard"
import { getDialogTitle } from "../shared/gameOutcome"

interface Props {
    gameState: any
    sendMoveHandler: (message: GameMoveMessage) => void
    opponent: User | null
}

export function Battleships({ gameState, sendMoveHandler, opponent }: Props) {
    const userId = useAuthStore((state) => state.user?.id)
    const { data } = BattleshipsStateSchema.safeParse(gameState)
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

            <div className="flex w-full max-w-md flex-col items-stretch justify-center gap-4 sm:max-w-none sm:flex-row sm:gap-8">
                <div className="flex flex-col items-center gap-2 sm:w-[30rem]">
                    <span className="text-xs font-semibold tracking-widest text-muted-foreground uppercase">
                        Enemy waters
                    </span>
                    <GameBoard
                        grid={state.opponent_grid}
                        interactive={true}
                        yourTurn={state.your_turn}
                        isOver={isOver}
                        onCellClick={handleClick}
                    />
                </div>
                <div className="flex flex-col items-center gap-2 sm:w-[30rem]">
                    <span className="text-xs font-semibold tracking-widest text-muted-foreground uppercase">
                        Your fleet
                    </span>
                    <GameBoard
                        grid={state.your_grid}
                        interactive={false}
                        yourTurn={state.your_turn}
                        isOver={isOver}
                    />
                </div>
            </div>
        </div>
    )
}
