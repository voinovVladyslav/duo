import clsx from "clsx"

interface Props {
    isOver: boolean
    yourTurn: boolean
    text: string
}

const styles = {
    base: "rounded-full px-5 py-1.5 text-sm font-semibold transition-all",
    over: "bg-primary/20 text-primary",
    yourTurn: "bg-primary text-primary-foreground shadow-md",
    waiting: "bg-muted text-muted-foreground",
}

export function GameStatus({ isOver, yourTurn, text }: Props) {
    return (
        <div
            className={clsx(
                styles.base,
                isOver && styles.over,
                !isOver && yourTurn && styles.yourTurn,
                !isOver && !yourTurn && styles.waiting
            )}
        >
            {text}
        </div>
    )
}
