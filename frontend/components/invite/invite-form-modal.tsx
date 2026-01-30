"use client"

import { useState } from "react"
import { Button } from "@/components/ui/button"
import { Input } from "@/components/ui/input"
import { Label } from "@/components/ui/label"
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogHeader,
  DialogTitle,
  DialogTrigger,
} from "@/components/ui/dialog"
import { Mail, CheckCircle2, Plus } from "lucide-react"
import { apiRequest } from "@/lib/api/client"
import { useAuth } from "@/components/auth/auth-provider"

interface InviteFormModalProps {
  onSuccess?: () => void
}

export function InviteFormModal({ onSuccess }: InviteFormModalProps) {
  const [open, setOpen] = useState(false)
  const [email, setEmail] = useState("")
  const [isLoading, setIsLoading] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const [success, setSuccess] = useState(false)
  const { user } = useAuth()

  const validateEmail = (email: string) => {
    const emailRegex = /^[^\s@]+@[^\s@]+\.[^\s@]+$/
    return emailRegex.test(email)
  }

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault()
    setError(null)
    setSuccess(false)

    if (!email.trim()) {
      setError("Email is required")
      return
    }

    if (!validateEmail(email)) {
      setError("Please enter a valid email address")
      return
    }

    if (!user?.id) {
      setError("You must be logged in to send invitations")
      return
    }

    setIsLoading(true)

    try {
      await apiRequest("/invites", {
        method: "POST",
        body: JSON.stringify({
          email: email.trim(),
          issued_by: user.id,
        }),
      })
      setSuccess(true)
      setEmail("")
      onSuccess?.()
      // Close modal after 2 seconds
      setTimeout(() => {
        setOpen(false)
        setSuccess(false)
      }, 2000)
    } catch (err: any) {
      setError(err.message || "Failed to send invitation. Please try again.")
    } finally {
      setIsLoading(false)
    }
  }

  return (
    <Dialog open={open} onOpenChange={setOpen}>
      <DialogTrigger asChild>
        <Button>
          <Plus className="h-4 w-4 mr-2" />
          Invite Candidate
        </Button>
      </DialogTrigger>
      <DialogContent className="sm:max-w-[500px]">
        <DialogHeader>
          <DialogTitle className="flex items-center gap-2">
            <Mail className="h-5 w-5" />
            Send Invitation
          </DialogTitle>
          <DialogDescription>
            Invite a candidate to apply for a position
          </DialogDescription>
        </DialogHeader>
        <form onSubmit={handleSubmit} className="space-y-4">
          {error && (
            <div className="rounded-md bg-destructive/15 p-3 text-sm text-destructive">
              {error}
            </div>
          )}
          {success && (
            <div className="rounded-md bg-green-500/15 p-3 text-sm text-green-600 dark:text-green-400 flex items-center gap-2">
              <CheckCircle2 className="h-4 w-4" />
              Invitation sent successfully!
            </div>
          )}

          <div className="space-y-2">
            <Label htmlFor="email">Candidate Email</Label>
            <Input
              id="email"
              type="email"
              placeholder="candidate@example.com"
              value={email}
              onChange={(e) => setEmail(e.target.value)}
              required
              disabled={isLoading}
            />
            <p className="text-xs text-muted-foreground">
              Enter the email address of the candidate you want to invite
            </p>
          </div>

          <div className="flex justify-end gap-2 pt-4">
            <Button
              type="button"
              variant="outline"
              onClick={() => setOpen(false)}
              disabled={isLoading}
            >
              Cancel
            </Button>
            <Button type="submit" disabled={isLoading}>
              {isLoading ? "Sending..." : "Send Invite"}
            </Button>
          </div>
        </form>
      </DialogContent>
    </Dialog>
  )
}


