"use client"

import { useState } from "react"
import { Button } from "@/components/ui/button"
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogHeader,
  DialogTitle,
  DialogTrigger,
} from "@/components/ui/dialog"
import { JobForm } from "./job-form"
import { Pencil } from "lucide-react"
import { apiRequest } from "@/lib/api/client"
import type { Job } from "@/lib/types/api"

interface EditJobButtonProps {
  job: Job
  onSuccess?: () => void
}

export function EditJobButton({ job, onSuccess }: EditJobButtonProps) {
  const [open, setOpen] = useState(false)
  const [isLoading, setIsLoading] = useState(false)

  const handleSubmit = async (formData: FormData) => {
    setIsLoading(true)
    try {
      const title = formData.get("title") as string
      const description = formData.get("description") as string
      const status = formData.get("status") as "open" | "closed"

      await apiRequest(`/jobs/${job.id}`, {
        method: "PUT",
        body: JSON.stringify({ title, description, status }),
      })
      setOpen(false)
      onSuccess?.()
    } catch (error) {
      throw error
    } finally {
      setIsLoading(false)
    }
  }

  return (
    <Dialog open={open} onOpenChange={setOpen}>
      <DialogTrigger asChild>
        <Button variant="ghost" size="icon">
          <Pencil className="h-4 w-4" />
        </Button>
      </DialogTrigger>
      <DialogContent className="sm:max-w-[500px]">
        <DialogHeader>
          <DialogTitle>Edit Job</DialogTitle>
          <DialogDescription>
            Update the job posting details.
          </DialogDescription>
        </DialogHeader>
        <JobForm
          job={job}
          onSubmit={handleSubmit}
          onCancel={() => setOpen(false)}
          isLoading={isLoading}
        />
      </DialogContent>
    </Dialog>
  )
}

