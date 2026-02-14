"use client"

import { useEffect, useState } from "react"
import { useParams } from "next/navigation"
import { ApplicationForm } from "@/components/apply/application-form"
import { ErrorPage } from "@/components/apply/error-page"

export default function ApplyTokenPage() {
  const params = useParams<{ token: string }>()
  const token = params?.token

  const [isValidating, setIsValidating] = useState(true)
  const [isValid, setIsValid] = useState(false)
  const [email, setEmail] = useState<string | null>(null)
  const [error, setError] = useState<string | null>(null)

  useEffect(() => {
    if (!token) {
      setError("Invalid invitation link")
      setIsValidating(false)
      return
    }

    const validateToken = async () => {
      try {
        const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL || "http://localhost:3001/api"
        const response = await fetch(`${API_BASE_URL}/apply/validate?token=${token}`)
        const data = await response.json()

        if (data.valid) {
          setIsValid(true)
          setEmail(data.email)
        } else {
          setIsValid(false)
          setError(data.error || "Invalid token")
        }
      } catch {
        setIsValid(false)
        setError("Failed to validate invitation link")
      } finally {
        setIsValidating(false)
      }
    }

    validateToken()
  }, [token])

  if (isValidating) {
    return (
      <div className="min-h-screen flex items-center justify-center">
        <div className="text-center">
          <div className="inline-block h-8 w-8 animate-spin rounded-full border-4 border-solid border-current border-r-transparent align-[-0.125em] motion-reduce:animate-[spin_1.5s_linear_infinite]" />
          <p className="mt-4 text-muted-foreground">Validating invitation...</p>
        </div>
      </div>
    )
  }

  if (!isValid || !email || !token) {
    let errorType: "invalid" | "expired" | "used" | "generic" = "generic"
    if (error?.includes("expired")) errorType = "expired"
    else if (error?.includes("used")) errorType = "used"
    else if (error?.includes("invalid")) errorType = "invalid"

    return <ErrorPage errorType={errorType} message={error || undefined} />
  }

  return <ApplicationForm token={token} email={email} />
}
