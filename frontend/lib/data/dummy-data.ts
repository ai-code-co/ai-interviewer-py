export interface DummyJob {
  id: string
  title: string
  status: 'open' | 'closed'
  created_at: string
}

export interface DummyInvite {
  email: string
  status: 'PENDING' | 'USED' | 'EXPIRED'
  sent_at: string
}

export interface DummyCandidate {
  name: string
  email: string
  replied: boolean
  job_title: string
}

export const dummyJobs: DummyJob[] = [
  { id: '1', title: 'Senior Full Stack Developer', status: 'open', created_at: '2024-01-15T10:00:00Z' },
  { id: '2', title: 'Frontend React Developer', status: 'open', created_at: '2024-01-18T14:30:00Z' },
  { id: '3', title: 'Backend Node.js Engineer', status: 'open', created_at: '2024-01-20T09:15:00Z' },
  { id: '4', title: 'DevOps Engineer', status: 'closed', created_at: '2024-01-10T11:20:00Z' },
  { id: '5', title: 'UI/UX Designer', status: 'open', created_at: '2024-01-22T16:45:00Z' },
  { id: '6', title: 'Product Manager', status: 'open', created_at: '2024-01-25T08:30:00Z' },
]

export const dummyInvites: DummyInvite[] = [
  { email: 'john.doe@example.com', status: 'PENDING', sent_at: '2024-01-20T10:00:00Z' },
  { email: 'jane.smith@example.com', status: 'USED', sent_at: '2024-01-19T14:30:00Z' },
  { email: 'bob.wilson@example.com', status: 'PENDING', sent_at: '2024-01-21T09:15:00Z' },
  { email: 'alice.brown@example.com', status: 'EXPIRED', sent_at: '2024-01-15T11:20:00Z' },
  { email: 'charlie.davis@example.com', status: 'USED', sent_at: '2024-01-18T16:45:00Z' },
  { email: 'diana.miller@example.com', status: 'PENDING', sent_at: '2024-01-22T08:30:00Z' },
  { email: 'edward.garcia@example.com', status: 'PENDING', sent_at: '2024-01-23T12:00:00Z' },
  { email: 'fiona.jones@example.com', status: 'USED', sent_at: '2024-01-17T15:30:00Z' },
  { email: 'george.martinez@example.com', status: 'PENDING', sent_at: '2024-01-24T10:15:00Z' },
  { email: 'helen.taylor@example.com', status: 'EXPIRED', sent_at: '2024-01-14T13:45:00Z' },
  { email: 'ivan.anderson@example.com', status: 'PENDING', sent_at: '2024-01-25T09:00:00Z' },
  { email: 'julia.thomas@example.com', status: 'USED', sent_at: '2024-01-16T11:30:00Z' },
  { email: 'kevin.jackson@example.com', status: 'PENDING', sent_at: '2024-01-26T14:20:00Z' },
]

export const dummyCandidates: DummyCandidate[] = [
  { name: 'John Doe', email: 'john.doe@example.com', replied: true, job_title: 'Senior Full Stack Developer' },
  { name: 'Jane Smith', email: 'jane.smith@example.com', replied: true, job_title: 'Frontend React Developer' },
  { name: 'Bob Wilson', email: 'bob.wilson@example.com', replied: false, job_title: 'Backend Node.js Engineer' },
  { name: 'Alice Brown', email: 'alice.brown@example.com', replied: true, job_title: 'UI/UX Designer' },
  { name: 'Charlie Davis', email: 'charlie.davis@example.com', replied: true, job_title: 'Product Manager' },
  { name: 'Diana Miller', email: 'diana.miller@example.com', replied: false, job_title: 'Senior Full Stack Developer' },
  { name: 'Edward Garcia', email: 'edward.garcia@example.com', replied: true, job_title: 'Frontend React Developer' },
  { name: 'Fiona Jones', email: 'fiona.jones@example.com', replied: true, job_title: 'Backend Node.js Engineer' },
]

// Calculate stats
export const stats = {
  totalJobs: dummyJobs.filter(job => job.status === 'open').length,
  candidatesInvited: dummyInvites.length,
  candidatesReplied: dummyCandidates.filter(c => c.replied).length,
  pendingInvitations: dummyInvites.filter(i => i.status === 'PENDING').length,
}

