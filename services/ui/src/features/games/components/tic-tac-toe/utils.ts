import type { Move } from "@/features/games/types/tic-tac-toe"

export function opponentSymbol(yourSymbol: Move): Move {
    return yourSymbol === "x" ? "o" : "x"
}
