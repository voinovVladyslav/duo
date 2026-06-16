import { describe, expect, it } from "vitest"
import { getStatusText, getDialogTitle } from "../../shared/gameOutcome"
import { opponentSymbol } from "../utils"
import type { TicTacToeState } from "@/features/games/types/tic-tac-toe"

const board: TicTacToeState["board"] = [
    [null, null, null],
    [null, null, null],
    [null, null, null],
]

const baseState: TicTacToeState = {
    board,
    your_turn: true,
    your_symbol: "x",
    is_draw: false,
    winner: null,
}

describe("opponentSymbol", () => {
    it("returns o for x", () => expect(opponentSymbol("x")).toBe("o"))
    it("returns x for o", () => expect(opponentSymbol("o")).toBe("x"))
})

describe("getStatusText", () => {
    it("your turn", () => {
        expect(getStatusText({ ...baseState, your_turn: true }, 1)).toBe(
            "Your turn"
        )
    })
    it("opponent turn", () => {
        expect(getStatusText({ ...baseState, your_turn: false }, 1)).toBe(
            "Opponent's turn"
        )
    })
    it("draw", () => {
        expect(getStatusText({ ...baseState, is_draw: true }, 1)).toBe(
            "It's a draw!"
        )
    })
    it("you win", () => {
        expect(getStatusText({ ...baseState, winner: 1 }, 1)).toBe("You win!")
    })
    it("opponent wins", () => {
        expect(getStatusText({ ...baseState, winner: 2 }, 1)).toBe(
            "Opponent wins!"
        )
    })
})

describe("getDialogTitle", () => {
    it("empty when game in progress", () => {
        expect(getDialogTitle(baseState, 1)).toBe("")
    })
    it("draw", () => {
        expect(getDialogTitle({ ...baseState, is_draw: true }, 1)).toBe(
            "It's a draw!"
        )
    })
    it("you win", () => {
        expect(getDialogTitle({ ...baseState, winner: 1 }, 1)).toBe("You win!")
    })
    it("you lost", () => {
        expect(getDialogTitle({ ...baseState, winner: 2 }, 1)).toBe("You lost!")
    })
})
