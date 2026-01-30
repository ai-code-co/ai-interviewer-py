import { createClient } from '@/lib/supabase/server'
import { NextResponse } from 'next/server'

export async function GET(request: Request) {
  const requestUrl = new URL(request.url)
  const code = requestUrl.searchParams.get('code')
  const next = requestUrl.searchParams.get('next') ?? '/dashboard'
  const origin = requestUrl.origin

  if (code) {
    const supabase = await createClient()
    const { error } = await supabase.auth.exchangeCodeForSession(code)
    
    if (!error) {
      // Successfully exchanged code for session, redirect to dashboard
      return NextResponse.redirect(`${origin}${next}`)
    } else {
      // Log error for debugging
      console.error('Error exchanging code for session:', error)
      // Redirect to login with error message
      return NextResponse.redirect(`${origin}/login?error=auth_failed`)
    }
  }

  // No code provided, redirect to login
  return NextResponse.redirect(`${origin}/login?error=no_code`)
}

