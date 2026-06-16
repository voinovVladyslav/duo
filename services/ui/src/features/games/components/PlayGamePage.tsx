import { TicTacToe } from "@/features/games/components/tic-tac-toe/TicTacToe"
import { Battleships } from "@/features/games/components/battleships/Battleships"
import { WaitingForOpponent } from "@/features/games/components/WaitingForOpponent"
import { useFetchGame } from "@/features/games/hooks/useFetchGame"
import { useGameWebSocket } from "@/features/games/hooks/useGameWebSocket"
import { useGetUser } from "@/features/auth/hooks/useGetUser"
import useAuthStore from "@/features/auth/stores/auth"
import { PageLoading } from "@/shared/components/layout/PageLoading"
import { useEffect, useState } from "react"
import { useNavigate, useParams } from "react-router"
import type { Game } from "@/features/games/types/game"
import type { User } from "@/features/auth/types/user"

export function PlayGamePage() {
    const navigate = useNavigate()
    const { id } = useParams()
    const [game, setGame] = useState<Game | null>(null)
    const [opponent, setOpponent] = useState<User | null>(null)
    const { loading, fetch } = useFetchGame()
    const { getUser } = useGetUser()
    const currentUser = useAuthStore((state) => state.user)
    const token = useAuthStore((state) => state.token)

    const { gameState, sendMessage } = useGameWebSocket(id!, token)

    useEffect(() => {
        const startup = async () => {
            const game = await fetch(Number(id))
            if (!game) {
                navigate("/")
                return
            }
            setGame(game)
        }
        startup()
        // eslint-disable-next-line react-hooks/exhaustive-deps
    }, [id])

    useEffect(() => {
        if (!gameState || !currentUser || opponent) return
        const resolveOpponent = async () => {
            const updatedGame = await fetch(Number(id))
            if (!updatedGame) return
            setGame(updatedGame)
            const opponentId =
                updatedGame.player1 === currentUser.id
                    ? updatedGame.player2
                    : updatedGame.player1
            if (!opponentId) return
            const user = await getUser(opponentId)
            if (user) setOpponent(user)
        }
        resolveOpponent()
        // eslint-disable-next-line react-hooks/exhaustive-deps
    }, [gameState])

    if (loading) return <PageLoading />
    if (!game) return null
    if (!gameState) return <WaitingForOpponent />

    return (
        <div className="flex w-full items-start justify-center">
            {game.type === "tic_tac_toe" && (
                <TicTacToe
                    gameState={gameState}
                    sendMoveHandler={sendMessage}
                    opponent={opponent}
                />
            )}
            {game.type === "battleships" && (
                <Battleships
                    gameState={gameState}
                    sendMoveHandler={sendMessage}
                    opponent={opponent}
                />
            )}
        </div>
    )
}
