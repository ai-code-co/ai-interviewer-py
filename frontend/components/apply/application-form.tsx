"use client"

import { useState, useEffect } from "react"
import { useRouter } from "next/navigation"
import { Button } from "@/components/ui/button"
import { Input } from "@/components/ui/input"
import { Label } from "@/components/ui/label"
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select"
import {
  Card,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle,
} from "@/components/ui/card"
import { Upload, FileText } from "lucide-react"

interface ApplicationFormProps {
  token: string
  email: string
}

interface Job {
  id: string
  title: string
  description: string | null
}

export function ApplicationForm({ token, email }: ApplicationFormProps) {
  const router = useRouter()
  const [name, setName] = useState("")
  const [phone, setPhone] = useState("")
  const [jobId, setJobId] = useState("")
  const [resume, setResume] = useState<File | null>(null)
  const [jobs, setJobs] = useState<Job[]>([])
  const [isLoading, setIsLoading] = useState(true)
  const [isSubmitting, setIsSubmitting] = useState(false)
  const [error, setError] = useState<string | null>(null)

  // Fetch jobs on mount
  useEffect(() => {
    const fetchJobs = async () => {
      try {
        const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:3001/api'
        const response = await fetch(`${API_BASE_URL}/invites/public/jobs`)
        if (response.ok) {
          const data = await response.json()
          setJobs(data)
        } else {
          setError("Failed to load jobs. Please refresh the page.")
        }
      } catch (err) {
        setError("Failed to load jobs. Please refresh the page.")
      } finally {
        setIsLoading(false)
      }
    }

    fetchJobs()
  }, [])

  const validatePhone = (phone: string) => {
    if (!phone) return true // Optional
    const phoneRegex = /^[\d\s\-\+\(\)]+$/
    return phoneRegex.test(phone)
  }

  const handleFileChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0]
    if (!file) return

    // Validate file type
    const allowedTypes = [
      "application/pdf",
      "application/msword",
      "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
    ]
    if (!allowedTypes.includes(file.type)) {
      setError("Please upload a PDF or Word document (.pdf, .doc, .docx)")
      return
    }

    // Validate file size (5MB)
    const maxSize = 5 * 1024 * 1024 // 5MB in bytes
    if (file.size > maxSize) {
      setError("File size must be less than 5MB")
      return
    }

    setResume(file)
    setError(null)
  }

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault()
    setError(null)

    // Validation
    if (!name.trim() || name.trim().length < 2) {
      setError("Name must be at least 2 characters")
      return
    }

    if (phone && !validatePhone(phone)) {
      setError("Please enter a valid phone number")
      return
    }

    if (!jobId) {
      setError("Please select a job")
      return
    }

    if (!resume) {
      setError("Please upload your resume")
      return
    }

    setIsSubmitting(true)

    try {
      const formData = new FormData()
      formData.append("email", email)
      formData.append("name", name.trim())
      formData.append("phone", phone.trim() || "")
      formData.append("job_id", jobId)
      formData.append("resume", resume)

      const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:3001/api'
      const response = await fetch(`${API_BASE_URL}/apply/submit`, {
        method: "POST",
        headers: {
          "X-Application-Token": token,
        },
        body: formData,
      })

      // Parse response - handle both JSON and non-JSON responses
      let data
      try {
        data = await response.json()
      } catch (parseError) {
        // If response is not JSON, create error object
        const text = await response.text()
        throw new Error(text || "Failed to submit application")
      }

      // Check if response is not ok (4xx, 5xx status codes)
      if (!response.ok) {
        // Extract error message from response
        const errorMessage = data?.error || data?.message || `Failed to submit application (${response.status})`
        throw new Error(errorMessage)
      }

      // Only redirect to success if we got here (response was ok)
      router.push("/apply/success")
    } catch (err: any) {
      // Display error message to user
      const errorMessage = err.message || "Failed to submit application. Please try again."
      setError(errorMessage)
      console.error("Application submission error:", err)
    } finally {
      setIsSubmitting(false)
    }
  }

  if (isLoading) {
    return (
      <div className="min-h-screen flex items-center justify-center p-4">
        <div className="text-center">
          <div className="inline-block h-8 w-8 animate-spin rounded-full border-4 border-solid border-current border-r-transparent align-[-0.125em] motion-reduce:animate-[spin_1.5s_linear_infinite]" />
          <p className="mt-4 text-muted-foreground">Loading application form...</p>
        </div>
      </div>
    )
  }

  return (
    <div className="min-h-screen flex items-center justify-center p-4 bg-muted/50">
      <Card className="w-full max-w-2xl">
        <CardHeader>
          <CardTitle>Application Form</CardTitle>
          <CardDescription>
            Please fill out the form below to submit your application
          </CardDescription>
        </CardHeader>
        <CardContent>
          <form onSubmit={handleSubmit} className="space-y-6">
            {error && (
              <div className="rounded-md bg-destructive/15 p-3 text-sm text-destructive">
                {error}
              </div>
            )}

            {/* Email (pre-filled, disabled) */}
            <div className="space-y-2">
              <Label htmlFor="email">Email (from invitation)</Label>
              <Input
                id="email"
                type="email"
                value={email}
                disabled
                className="bg-muted"
              />
              <p className="text-xs text-muted-foreground">
                This email is from your invitation and cannot be changed
              </p>
            </div>

            {/* Name */}
            <div className="space-y-2">
              <Label htmlFor="name">
                Full Name <span className="text-destructive">*</span>
              </Label>
              <Input
                id="name"
                type="text"
                value={name}
                onChange={(e) => setName(e.target.value)}
                placeholder="Enter your full name"
                required
                disabled={isSubmitting}
                minLength={2}
              />
            </div>

            {/* Phone */}
            <div className="space-y-2">
              <Label htmlFor="phone">Phone Number</Label>
              <Input
                id="phone"
                type="tel"
                value={phone}
                onChange={(e) => setPhone(e.target.value)}
                placeholder="Enter your phone number (optional)"
                disabled={isSubmitting}
              />
            </div>

            {/* Job Selection */}
            <div className="space-y-2">
              <Label htmlFor="job">
                Select Position <span className="text-destructive">*</span>
              </Label>
              <Select
                value={jobId}
                onValueChange={setJobId}
                disabled={isSubmitting}
              >
                <SelectTrigger id="job">
                  <SelectValue placeholder="Select a job position" />
                </SelectTrigger>
                <SelectContent>
                  {jobs.map((job) => (
                    <SelectItem key={job.id} value={job.id}>
                      {job.title}
                    </SelectItem>
                  ))}
                </SelectContent>
              </Select>
              {jobs.length === 0 && (
                <p className="text-xs text-muted-foreground">
                  No open positions available at the moment
                </p>
              )}
            </div>

            {/* Resume Upload */}
            <div className="space-y-2">
              <Label htmlFor="resume">
                Resume <span className="text-destructive">*</span>
              </Label>
              <div className="flex items-center gap-4">
                <Input
                  id="resume"
                  type="file"
                  accept=".pdf,.doc,.docx,application/pdf,application/msword,application/vnd.openxmlformats-officedocument.wordprocessingml.document"
                  onChange={handleFileChange}
                  disabled={isSubmitting}
                  className="cursor-pointer"
                />
              </div>
              {resume && (
                <div className="flex items-center gap-2 p-3 bg-muted rounded-md">
                  <FileText className="h-4 w-4" />
                  <span className="text-sm">{resume.name}</span>
                  <span className="text-xs text-muted-foreground">
                    ({(resume.size / 1024 / 1024).toFixed(2)} MB)
                  </span>
                </div>
              )}
              <p className="text-xs text-muted-foreground">
                Accepted formats: PDF, DOC, DOCX (Max size: 5MB)
              </p>
            </div>

            <Button type="submit" className="w-full" disabled={isSubmitting}>
              {isSubmitting ? "Submitting..." : "Submit Application"}
            </Button>
          </form>
        </CardContent>
      </Card>
    </div>
  )
}

