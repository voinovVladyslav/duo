import type { User } from "@/features/auth/types/user"
import type { GameMoveMessage } from "@/features/games/types/game"

interface Props {
    gameState: any,
    sendMoveHandler: (message: GameMoveMessage) => void
    opponent: User | null
}

export function Battleships({ gameState, sendMoveHandler, opponent }: Props) {
    return (<div>Battleships</div>)
}
