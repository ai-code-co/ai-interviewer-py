import Link from "next/link"
import { Button } from "@/components/ui/button"
import { ThemeToggle } from "@/components/theme-toggle"
import {
  Card,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle,
} from "@/components/ui/card"
import { createClient } from "@/lib/supabase/server"
import { redirect } from "next/navigation"

export default async function Home() {
  const supabase = await createClient()
  const {
    data: { user },
  } = await supabase.auth.getUser()

  return (
    <div className="min-h-screen flex flex-col">
      <header className="border-b">
        <div className="container mx-auto px-4 py-4 flex items-center justify-between">
          <h1 className="text-2xl font-bold">AI Interviewer</h1>
          <div className="flex items-center gap-4">
            <ThemeToggle />
            {user ? (
              <Link href="/dashboard">
                <Button>Go to Dashboard</Button>
              </Link>
            ) : (
              <div className="flex gap-2">
                <Link href="/login">
                  <Button variant="outline">Sign in</Button>
                </Link>
                <Link href="/register">
                  <Button>Sign up</Button>
                </Link>
              </div>
            )}
          </div>
        </div>
      </header>
      <main className="flex-1 flex items-center justify-center p-4">
        <Card className="w-full max-w-2xl">
          <CardHeader className="text-center">
            <CardTitle className="text-4xl font-bold">
              Welcome to AI Interviewer
            </CardTitle>
            <CardDescription className="text-lg">
              Your intelligent interview platform powered by AI
            </CardDescription>
          </CardHeader>
          <CardContent className="space-y-6">
            <div className="text-center space-y-2">
              {user ? (
                <>
                  <p className="text-muted-foreground">
                    You are signed in as {user.email}
                  </p>
                  <Link href="/dashboard">
                    <Button size="lg" className="mt-4">
                      Go to Dashboard
                    </Button>
                  </Link>
                </>
              ) : (
                <>
                  <p className="text-muted-foreground">
                    Get started by creating an account or signing in
                  </p>
                  <div className="flex gap-4 justify-center mt-6">
                    <Link href="/register">
                      <Button size="lg">Create Account</Button>
                    </Link>
                    <Link href="/login">
                      <Button size="lg" variant="outline">
                        Sign In
                      </Button>
                    </Link>
                  </div>
                </>
              )}
            </div>
          </CardContent>
        </Card>
    </main>
    </div>
  )
}
