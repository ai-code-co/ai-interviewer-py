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
import { Plus } from "lucide-react"
import { apiRequest } from "@/lib/api/client"

interface AddJobButtonProps {
  onSuccess?: () => void
}

export function AddJobButton({ onSuccess }: AddJobButtonProps) {
  const [open, setOpen] = useState(false)
  const [isLoading, setIsLoading] = useState(false)

  const handleSubmit = async (formData: FormData) => {
    setIsLoading(true)
    try {
      const title = formData.get("title") as string
      const description = formData.get("description") as string
      const status = formData.get("status") as "open" | "closed"

      await apiRequest("/jobs", {
        method: "POST",
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
        <Button>
          <Plus className="h-4 w-4 mr-2" />
          Add Job
        </Button>
      </DialogTrigger>
      <DialogContent className="sm:max-w-[500px]">
        <DialogHeader>
          <DialogTitle>Create New Job</DialogTitle>
          <DialogDescription>
            Add a new job posting to your recruitment system.
          </DialogDescription>
        </DialogHeader>
        <JobForm
          onSubmit={handleSubmit}
          onCancel={() => setOpen(false)}
          isLoading={isLoading}
        />
      </DialogContent>
    </Dialog>
  )
}

