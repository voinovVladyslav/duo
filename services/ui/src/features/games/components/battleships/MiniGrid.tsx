import type { Cell } from "@/features/games/types/battleships"
import { BattleshipsCell } from "./BattleshipsCell"

// prettier-ignore
const GRID_MARKS: Cell[] = [
    "b", "b", "",  "",  "m",
    "",  "",  "",  "x", "",
    "",  "s", "s", "",  "",
    "b", "",  "",  "",  "m",
    "b", "",  "m", "",  "x",
]

const tone: Record<string, string> = {
    b: "border-primary/50 bg-primary/10",
    x: "border-rose-500/60 bg-rose-500/15",
    s: "border-rose-600 bg-rose-600/20",
}

export function BattleshipsMiniGrid() {
    return (
        <div className="relative mx-auto grid aspect-square w-48 grid-cols-5 grid-rows-5 gap-[3px] sm:w-36">
            {GRID_MARKS.map((value, i) => (
                <div
                    key={i}
                    className={`flex items-center justify-center rounded-[3px] border border-transparent bg-white/5 ${tone[value] ?? ""}`}
                >
                    <BattleshipsCell
                        value={value}
                        className="size-4 stroke-[2.5] sm:size-3.5"
                    />
                </div>
            ))}
            <div className="pointer-events-none absolute inset-0 rounded-sm ring-1 ring-white/10" />
        </div>
    )
}
