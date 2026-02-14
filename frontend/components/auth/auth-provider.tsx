"use client"

import { createContext, useContext, useState } from "react"
import { useRouter } from "next/navigation"

export type LocalUser = {
  id: string
  email: string
}

type AuthContextType = {
  user: LocalUser | null
  loading: boolean
  signIn: (email: string) => Promise<void>
  signUp: (email: string) => Promise<void>
  signOut: () => Promise<void>
}

const STORAGE_KEY = "ai_interviewer_auth_user"
const DEFAULT_USER: LocalUser = {
  id: "00000000-0000-0000-0000-000000000001",
  email: "admin@local.test",
}

const AuthContext = createContext<AuthContextType>({
  user: null,
  loading: true,
  signIn: async () => {},
  signUp: async () => {},
  signOut: async () => {},
})

function loadUser(): LocalUser | null {
  if (typeof window === "undefined") return null
  const raw = window.localStorage.getItem(STORAGE_KEY)
  if (!raw) return null
  try {
    const parsed = JSON.parse(raw) as LocalUser
    if (parsed?.id && parsed?.email) return parsed
    return null
  } catch {
    return null
  }
}

function saveUser(user: LocalUser) {
  if (typeof window === "undefined") return
  window.localStorage.setItem(STORAGE_KEY, JSON.stringify(user))
}

function clearUser() {
  if (typeof window === "undefined") return
  window.localStorage.removeItem(STORAGE_KEY)
}

export function AuthProvider({ children }: { children: React.ReactNode }) {
  const [user, setUser] = useState<LocalUser | null>(() => {
    if (typeof window === "undefined") return DEFAULT_USER
    const persisted = loadUser()
    if (persisted) return persisted
    saveUser(DEFAULT_USER)
    return DEFAULT_USER
  })
  const router = useRouter()

  const signIn = async (email: string) => {
    const existing = loadUser()
    const nextUser: LocalUser = {
      id: existing?.id || DEFAULT_USER.id,
      email,
    }
    saveUser(nextUser)
    setUser(nextUser)
    router.refresh()
  }

  const signUp = async (email: string) => {
    await signIn(email)
  }

  const signOut = async () => {
    clearUser()
    setUser(null)
    router.push("/login")
    router.refresh()
  }

  return (
    <AuthContext.Provider value={{ user, loading: false, signIn, signUp, signOut }}>
      {children}
    </AuthContext.Provider>
  )
}

export const useAuth = () => useContext(AuthContext)
