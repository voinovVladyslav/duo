import { z } from "zod"

export const CellSchema = z.enum(["", "b", "x", "m"])
export const GridSchema = z.array(z.array(CellSchema).length(10)).length(10)
export const BattleshipsStateSchema = z.object({
    your_turn: z.boolean(),
    your_grid: GridSchema,
    opponent_grid: GridSchema,
    winner: z.int().nullable(),
    is_draw: z.boolean(),
})

export type Grid = z.infer<typeof GridSchema>
export type Cell = z.infer<typeof CellSchema>
export type BattleshipsState = z.infer<typeof BattleshipsStateSchema>
