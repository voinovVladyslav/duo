import type { Cell } from "@/features/games/types/battleships"
import { Dot, Flame, Ship } from "lucide-react"

interface Props {
    value: Cell
    className?: string
}

export function BattleshipsCell({
    value,
    className = "size-5 stroke-[2.5]",
}: Props) {
    if (value === "b") return <Ship className={`${className} text-primary`} />
    if (value === "x") return <Flame className={`${className} text-rose-500`} />
    if (value === "m")
        return <Dot className={`${className} text-muted-foreground`} />
    return null
}
