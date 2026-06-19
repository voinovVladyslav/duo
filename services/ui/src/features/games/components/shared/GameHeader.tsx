import type { ReactNode } from "react"
import { GameStatus } from "./GameStatus"

interface Props {
    title: string
    opponentName: string
    yourTurn: boolean
    isOver: boolean
    statusText: string
    youSlot?: ReactNode
    opponentSlot?: ReactNode
}

export function GameHeader({
    title,
    opponentName,
    yourTurn,
    isOver,
    statusText,
    youSlot,
    opponentSlot,
}: Props) {
    return (
        <div className="flex flex-col items-center gap-2">
            <h2 className="text-lg font-bold tracking-tight">{title}</h2>
            <div className="grid grid-cols-[1fr_auto_1fr] items-center gap-2">
                <div
                    className={`flex items-center justify-end gap-1.5 transition-opacity ${!isOver && yourTurn ? "opacity-100" : "opacity-40"}`}
                >
                    <span className="text-sm font-medium text-foreground">
                        You
                    </span>
                    {youSlot}
                </div>
                <span className="text-xs font-semibold tracking-widest text-muted-foreground uppercase">
                    vs
                </span>
                <div
                    className={`flex min-w-0 items-center justify-start gap-1.5 transition-opacity ${!isOver && !yourTurn ? "opacity-100" : "opacity-40"}`}
                >
                    {opponentSlot}
                    <span className="truncate text-sm font-medium text-foreground">
                        {opponentName}
                    </span>
                </div>
            </div>
            <GameStatus isOver={isOver} yourTurn={yourTurn} text={statusText} />
        </div>
    )
}
