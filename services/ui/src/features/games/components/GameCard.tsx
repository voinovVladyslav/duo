import type { ReactNode } from "react"

interface GameCardProps {
    title: string
    preview: ReactNode
    loading?: boolean
    onClick: () => void
}

export function GameCard({ title, preview, loading, onClick }: GameCardProps) {
    return (
        <button
            disabled={loading}
            onClick={onClick}
            className="group relative flex w-72 cursor-pointer flex-col gap-5 overflow-hidden rounded-xl border border-white/10 bg-card p-6 text-left transition-all duration-200 hover:border-primary/50 hover:shadow-[0_0_24px_oklch(0.696_0.17_162.48/0.15)] active:scale-[0.98] disabled:pointer-events-none disabled:opacity-50 sm:w-64"
        >
            <div className="absolute inset-0 bg-gradient-to-br from-primary/5 via-transparent to-transparent opacity-0 transition-opacity duration-200 group-hover:opacity-100" />
            {preview}
            <div className="relative flex flex-col gap-1 text-center">
                <span className="text-base font-semibold tracking-tight text-foreground sm:text-lg">
                    {title}
                </span>
            </div>
            <div className="relative mt-auto w-full rounded-lg bg-primary px-3 py-2 text-center text-sm font-medium text-primary-foreground transition-colors duration-150 group-hover:brightness-110">
                {loading ? "Creating…" : "Play"}
            </div>
        </button>
    )
}
