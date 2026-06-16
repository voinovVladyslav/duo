import { BattleshipsMiniGrid } from "@/features/games/components/battleships/MiniGrid"
import { GameCard } from "@/features/games/components/GameCard"
import { TicTacToeMiniGrid } from "@/features/games/components/tic-tac-toe/MiniGrid"
import { useCreateGame } from "@/features/games/hooks/useCreateGame"
import type { GameType } from "@/features/games/types/game"
import { useNavigate } from "react-router"

export function MainMenu() {
    const navigate = useNavigate()
    const { loading, create, error } = useCreateGame()

    const handleCreateGame = async (type: GameType) => {
        const game = await create({ type })
        if (game === null) {
            console.error("Failed to create game:", error)
            return
        }
        navigate(`/game/${game.id}`)
    }

    return (
        <div className="flex w-full items-start justify-center p-4 sm:justify-start sm:p-10">
            <div className="grid grid-cols-1 gap-4 sm:grid-cols-2 lg:grid-cols-3">
                <GameCard
                    title="Tic Tac Toe"
                    preview={<TicTacToeMiniGrid />}
                    loading={loading}
                    onClick={() => handleCreateGame("tic_tac_toe")}
                />
                <GameCard
                    title="Battleships"
                    preview={<BattleshipsMiniGrid />}
                    loading={loading}
                    onClick={() => handleCreateGame("battleships")}
                />
            </div>
        </div>
    )
}
