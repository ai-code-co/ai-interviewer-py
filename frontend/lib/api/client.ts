const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:3001/api'

export async function apiRequest<T>(
  endpoint: string,
  options: RequestInit = {}
): Promise<T> {
  const response = await fetch(`${API_BASE_URL}${endpoint}`, {
    ...options,
    headers: {
      'Content-Type': 'application/json',
      ...options.headers,
    },
  })

  if (!response.ok) {
    const error = await response.json().catch(() => ({ error: 'Request failed' }))
    throw new Error(error.error || 'Request failed')
  }

  // Handle 204 No Content
  if (response.status === 204) {
    return undefined as T
  }

  return response.json()
}

export async function updateCandidateStatus(
  candidateId: string,
  status: "APPROVED" | "REJECTED",
  customMessage?: string
): Promise<void> {
  await apiRequest<void>(`/candidates/${candidateId}/status`, {
    method: "PUT",
    body: JSON.stringify({ status, customMessage }),
  })
}

export async function apiFormData<T>(
  endpoint: string,
  formData: FormData,
  token?: string
): Promise<T> {
  const headers: HeadersInit = {}
  if (token) {
    headers['X-Application-Token'] = token
  }

  const response = await fetch(`${API_BASE_URL}${endpoint}`, {
    method: 'POST',
    body: formData,
    headers,
  })

  if (!response.ok) {
    const error = await response.json().catch(() => ({ error: 'Request failed' }))
    throw new Error(error.error || 'Request failed')
  }

  return response.json()
}

