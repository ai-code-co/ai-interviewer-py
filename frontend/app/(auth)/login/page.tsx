import { Suspense } from "react"
import { LoginForm } from "@/components/auth/login-form"
import { ThemeToggle } from "@/components/theme-toggle"

function LoginFormWrapper() {
  return <LoginForm />
}

export default function LoginPage() {
  return (
    <div className="min-h-screen flex flex-col">
      <div className="flex justify-end p-4">
        <ThemeToggle />
      </div>
      <div className="flex-1 flex items-center justify-center p-4">
        <Suspense fallback={<div>Loading...</div>}>
          <LoginFormWrapper />
        </Suspense>
      </div>
    </div>
  )
}

