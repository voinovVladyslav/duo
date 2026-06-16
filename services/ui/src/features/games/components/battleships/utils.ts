import type { BattleshipsState } from "@/features/games/types/battleships"

export function getStatusText(
    state: BattleshipsState,
    userId: number | undefined
): string {
    if (state.is_draw) return "It's a draw!"
    if (state.winner !== null)
        return state.winner === userId ? "You win!" : "Opponent wins!"
    return state.your_turn ? "Your turn" : "Opponent's turn"
}

export function getDialogTitle(
    state: BattleshipsState,
    userId: number | undefined
): string {
    if (state.is_draw) return "It's a draw!"
    if (state.winner !== null)
        return state.winner === userId ? "You win!" : "You lost!"
    return ""
}
