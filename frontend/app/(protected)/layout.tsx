import { AppSidebar } from "@/components/layout/app-sidebar"
import { ThemeToggle } from "@/components/theme-toggle"
import { createClient } from "@/lib/supabase/server"
import { redirect } from "next/navigation"

export default async function ProtectedLayout({
  children,
}: {
  children: React.ReactNode
}) {
  const supabase = await createClient()
  const {
    data: { user },
  } = await supabase.auth.getUser()

  if (!user) {
    redirect("/login")
  }

  return (
    <div className="min-h-screen flex">
      <AppSidebar />
      <div className="flex-1 flex flex-col lg:pl-64">
        <header className="sticky top-0 z-10 border-b bg-background/95 backdrop-blur supports-backdrop-filter:bg-background/60">
          <div className="container mx-auto px-4 py-4 flex items-center justify-between">
            <div className="flex-1" />
            <div className="flex items-center gap-4">
              <ThemeToggle />
            </div>
          </div>
        </header>
        <main className="flex-1 container mx-auto px-4 py-8">{children}</main>
      </div>
    </div>
  )
}

