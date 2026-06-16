import { TicTacToeCell } from "./TicTacToeCell"

const GRID_MARKS: ("x" | "o" | null)[] = [
    "x",
    "o",
    null,
    null,
    "x",
    "o",
    "o",
    null,
    "x",
]

export function TicTacToeMiniGrid() {
    return (
        <div className="relative mx-auto grid aspect-square w-48 grid-cols-3 grid-rows-3 gap-[3px] sm:w-36">
            {GRID_MARKS.map((value, i) => (
                <div
                    key={i}
                    className="flex items-center justify-center rounded-[3px] bg-white/5"
                >
                    <TicTacToeCell
                        value={value}
                        className="h-9 w-9 stroke-[3] sm:h-7 sm:w-7"
                    />
                </div>
            ))}
            <div className="pointer-events-none absolute inset-0 rounded-sm ring-1 ring-white/10" />
        </div>
    )
}
