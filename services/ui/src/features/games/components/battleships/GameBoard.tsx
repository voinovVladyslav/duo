import type { Grid } from "@/features/games/types/battleships"
import clsx from "clsx"
import { BattleshipsCell } from "./BattleshipsCell"

interface Props {
    grid: Grid
    interactive: boolean
    yourTurn: boolean
    isOver: boolean
    onCellClick?: (i: number, j: number) => void
}

const styles = {
    cell: {
        base: "flex h-7 w-7 items-center justify-center rounded-md border bg-card transition-all sm:h-8 sm:w-8",
        interactive:
            "cursor-pointer hover:border-primary/60 hover:bg-primary/10 active:scale-95",
        static: "cursor-default",
    },
}

export function GameBoard({
    grid,
    interactive,
    yourTurn,
    isOver,
    onCellClick,
}: Props) {
    return (
        <div className="grid grid-cols-10 gap-1">
            {grid.map((row, i) =>
                row.map((value, j) => {
                    const shot = value === "x" || value === "m"
                    const clickable =
                        interactive && yourTurn && !isOver && !shot
                    return (
                        <button
                            key={`${i}_${j}`}
                            onClick={() => clickable && onCellClick?.(i, j)}
                            disabled={!clickable}
                            className={clsx(
                                styles.cell.base,
                                clickable
                                    ? styles.cell.interactive
                                    : styles.cell.static
                            )}
                        >
                            <BattleshipsCell value={value} />
                        </button>
                    )
                })
            )}
        </div>
    )
}
