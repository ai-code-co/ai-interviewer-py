import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card"
import { AlertCircle, XCircle, Clock } from "lucide-react"
import { Button } from "@/components/ui/button"
import Link from "next/link"

interface ErrorPageProps {
  errorType?: "invalid" | "expired" | "used" | "generic"
  message?: string
}

export function ErrorPage({ errorType = "generic", message }: ErrorPageProps) {
  const getErrorContent = () => {
    switch (errorType) {
      case "invalid":
        return {
          icon: XCircle,
          title: "Invalid Invitation Link",
          description: "This invitation link is invalid or does not exist.",
        }
      case "expired":
        return {
          icon: Clock,
          title: "Invitation Expired",
          description: "This invitation link has expired. Please request a new invitation.",
        }
      case "used":
        return {
          icon: AlertCircle,
          title: "Invitation Already Used",
          description: "This invitation link has already been used.",
        }
      default:
        return {
          icon: AlertCircle,
          title: "Error",
          description: message || "An error occurred while processing your request.",
        }
    }
  }

  const { icon: Icon, title, description } = getErrorContent()

  return (
    <div className="min-h-screen flex items-center justify-center p-4">
      <Card className="w-full max-w-md">
        <CardHeader className="text-center">
          <div className="mx-auto mb-4 flex h-12 w-12 items-center justify-center rounded-full bg-destructive/10">
            <Icon className="h-6 w-6 text-destructive" />
          </div>
          <CardTitle>{title}</CardTitle>
          <CardDescription>{description}</CardDescription>
        </CardHeader>
      </Card>
    </div>
  )
}

