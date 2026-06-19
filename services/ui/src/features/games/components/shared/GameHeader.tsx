import clsx from "clsx"
import type { ReactNode } from "react"

interface Props {
    opponentName: string
    yourTurn: boolean
    isOver: boolean
    youSlot?: ReactNode
    opponentSlot?: ReactNode
}

const styles = {
    pill: "inline-flex min-w-0 items-center gap-1.5 rounded-full px-3 py-1 text-sm font-medium transition-all",
    active: "bg-primary text-primary-foreground shadow-sm",
    inactive: "bg-muted text-muted-foreground",
}

export function GameHeader({
    opponentName,
    yourTurn,
    isOver,
    youSlot,
    opponentSlot,
}: Props) {
    const youActive = !isOver && yourTurn
    const opponentActive = !isOver && !yourTurn

    return (
        <div className="grid grid-cols-[1fr_auto_1fr] items-center gap-2">
            <div className="flex min-w-0 justify-end">
                <span
                    className={clsx(
                        styles.pill,
                        youActive ? styles.active : styles.inactive
                    )}
                >
                    <span>You</span>
                    {youSlot}
                </span>
            </div>
            <span className="text-xs font-semibold tracking-widest text-muted-foreground uppercase">
                vs
            </span>
            <div className="flex min-w-0 justify-start">
                <span
                    className={clsx(
                        styles.pill,
                        opponentActive ? styles.active : styles.inactive
                    )}
                >
                    {opponentSlot}
                    <span className="truncate">{opponentName}</span>
                </span>
            </div>
        </div>
    )
}
