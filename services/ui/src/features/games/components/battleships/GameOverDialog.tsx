import { Button } from "@/components/ui/button"
import {
    Dialog,
    DialogContent,
    DialogDescription,
    DialogFooter,
    DialogHeader,
    DialogTitle,
} from "@/components/ui/dialog"
import { useNavigate } from "react-router"

interface Props {
    isOver: boolean
    title: string
}

export function GameOverDialog({ isOver, title }: Props) {
    const navigate = useNavigate()

    return (
        <Dialog open={isOver}>
            <DialogContent showCloseButton={false}>
                <DialogHeader>
                    <DialogTitle className="text-center text-2xl">
                        {title}
                    </DialogTitle>
                </DialogHeader>
                <DialogDescription className="sr-only">
                    Game over
                </DialogDescription>
                <DialogFooter className="sm:justify-center">
                    <Button onClick={() => navigate("/")}>
                        Back to main menu
                    </Button>
                </DialogFooter>
            </DialogContent>
        </Dialog>
    )
}
