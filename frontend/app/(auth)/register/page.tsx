import { RegisterForm } from "@/components/auth/register-form"
import { ThemeToggle } from "@/components/theme-toggle"

export default function RegisterPage() {
  return (
    <div className="min-h-screen flex flex-col">
      <div className="flex justify-end p-4">
        <ThemeToggle />
      </div>
      <div className="flex-1 flex items-center justify-center p-4">
        <RegisterForm />
      </div>
    </div>
  )
}

