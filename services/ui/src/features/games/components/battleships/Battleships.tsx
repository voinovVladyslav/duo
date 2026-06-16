import type { User } from "@/features/auth/types/user"
import type { GameMoveMessage } from "@/features/games/types/game"
import {
    BattleshipsStateSchema,
    type Cell,
} from "@/features/games/types/battleships"

interface Props {
    gameState: any
    sendMoveHandler: (message: GameMoveMessage) => void
    opponent: User | null
}
function Cell({ value }: { value: Cell }) {
    return <div className="size-5 border border-white">{value}</div>
}

export function Battleships({ gameState, sendMoveHandler, opponent }: Props) {
    const { data } = BattleshipsStateSchema.safeParse(gameState)
    if (data === undefined) {
        return <div>Failed to parse game state</div>
    }
    const state = data!

    const handleClick = (i: number, j: number) => {
        sendMoveHandler({
            type: "game_move",
            body: { game_move: { coordinate: [i, j] } },
        })
    }
    const onCellClick = (i: number, j: number) => {
        handleClick(i, j)
    }
    return (
        <div className="flex flex-col items-center gap-6 p-8">
            <div>Battleships</div>
            <div>{state.your_turn ? "yes" : "no"}</div>
            <div className="grid grid-cols-10 gap-2">
                {state.your_grid.map((row, i) =>
                    row.map((value, j) => (
                        <button key={`you_${i}_${j}`}>
                            <Cell value={value} />
                        </button>
                    ))
                )}
            </div>
            <div className="grid grid-cols-10 gap-2">
                {state.opponent_grid.map((row, i) =>
                    row.map((value, j) => (
                        <button
                            key={`opp_${i}_${j}`}
                            onClick={() => onCellClick(i, j)}
                        >
                            <Cell value={value} />
                        </button>
                    ))
                )}
            </div>
        </div>
    )
}
