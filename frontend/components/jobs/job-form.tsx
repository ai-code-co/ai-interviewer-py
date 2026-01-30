"use client"

import { useState, useEffect } from "react"
import { Button } from "@/components/ui/button"
import { Input } from "@/components/ui/input"
import { Label } from "@/components/ui/label"
import { Textarea } from "@/components/ui/textarea"
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select"
import type { Job } from "@/lib/types/api"

interface JobFormProps {
  job?: Job
  onSubmit: (formData: FormData) => Promise<void>
  onCancel: () => void
  isLoading?: boolean
}

export function JobForm({ job, onSubmit, onCancel, isLoading }: JobFormProps) {
  const [title, setTitle] = useState(job?.title || "")
  const [description, setDescription] = useState(job?.description || "")
  const [status, setStatus] = useState<"open" | "closed">(job?.status || "open")
  const [error, setError] = useState<string | null>(null)

  const handleSubmit = async (e: React.FormEvent<HTMLFormElement>) => {
    e.preventDefault()
    setError(null)

    if (!title.trim()) {
      setError("Title is required")
      return
    }

    if (!status) {
      setError("Status is required")
      return
    }

    const formData = new FormData()
    formData.append("title", title.trim())
    formData.append("description", description.trim())
    formData.append("status", status)

    try {
      await onSubmit(formData)
    } catch (err: any) {
      setError(err.message || "An error occurred")
    }
  }

  return (
    <form onSubmit={handleSubmit} className="space-y-4">
      {error && (
        <div className="rounded-md bg-destructive/15 p-3 text-sm text-destructive">
          {error}
        </div>
      )}

      <div className="space-y-2">
        <Label htmlFor="title">Title *</Label>
        <Input
          id="title"
          value={title}
          onChange={(e) => setTitle(e.target.value)}
          placeholder="Enter job title"
          required
          disabled={isLoading}
        />
      </div>

      <div className="space-y-2">
        <Label htmlFor="description">Description</Label>
        <Textarea
          id="description"
          value={description}
          onChange={(e) => setDescription(e.target.value)}
          placeholder="Enter job description"
          rows={4}
          disabled={isLoading}
          className="max-h-48 overflow-y-auto resize-none"
        />
      </div>

      <div className="space-y-2">
        <Label htmlFor="status">Status *</Label>
        <Select
          value={status}
          onValueChange={(value: "open" | "closed") => setStatus(value)}
          disabled={isLoading}
        >
          <SelectTrigger id="status">
            <SelectValue placeholder="Select status" />
          </SelectTrigger>
          <SelectContent>
            <SelectItem value="open">Open</SelectItem>
            <SelectItem value="closed">Closed</SelectItem>
          </SelectContent>
        </Select>
      </div>

      <div className="flex justify-end gap-2 pt-4">
        <Button type="button" variant="outline" onClick={onCancel} disabled={isLoading}>
          Cancel
        </Button>
        <Button type="submit" disabled={isLoading}>
          {isLoading ? "Saving..." : job ? "Update Job" : "Create Job"}
        </Button>
      </div>
    </form>
  )
}

