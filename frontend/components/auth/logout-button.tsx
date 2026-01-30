"use client"

import { useAuth } from "./auth-provider"
import { Button } from "@/components/ui/button"
import { LogOut } from "lucide-react"

export function LogoutButton() {
  const { signOut, loading } = useAuth()

  return (
    <Button
      variant="outline"
      onClick={signOut}
      disabled={loading}
      className="gap-2"
    >
      <LogOut className="h-4 w-4" />
      Sign out
    </Button>
  )
}

