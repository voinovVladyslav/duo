export interface GameOutcome {
    your_turn: boolean
    is_draw: boolean
    winner: number | null
}

export function getStatusText(
    state: GameOutcome,
    userId: number | undefined
): string {
    if (state.is_draw) return "It's a draw!"
    if (state.winner !== null)
        return state.winner === userId ? "You win!" : "Opponent wins!"
    return state.your_turn ? "Your turn" : "Opponent's turn"
}

export function getDialogTitle(
    state: GameOutcome,
    userId: number | undefined
): string {
    if (state.is_draw) return "It's a draw!"
    if (state.winner !== null)
        return state.winner === userId ? "You win!" : "You lost!"
    return ""
}
