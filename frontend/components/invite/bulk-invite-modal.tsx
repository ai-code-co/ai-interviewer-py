"use client"

import { useState } from "react"
import { Button } from "@/components/ui/button"
import { Dialog, DialogContent, DialogHeader, DialogTitle, DialogTrigger } from "@/components/ui/dialog"
import { Textarea } from "@/components/ui/textarea"
import { Users, Upload, Check, AlertCircle, Loader2, X } from "lucide-react"
import { apiRequest } from "@/lib/api/client"
import { useAuth } from "@/components/auth/auth-provider"

export function BulkInviteModal() {
  const [isOpen, setIsOpen] = useState(false)
  const [loading, setLoading] = useState(false)
  const [result, setResult] = useState<any>(null)
  
  // Two Modes: 'INPUT' (Typing) or 'REVIEW' (Checkboxes)
  const [mode, setMode] = useState<'INPUT' | 'REVIEW'>('INPUT')
  const [rawInput, setRawInput] = useState("")
  const [emailList, setEmailList] = useState<Array<{email: string, checked: boolean}>>([])

  const { user } = useAuth()

  const handleProcess = () => {
    const found = rawInput.split(/[\n,; ]+/).map(e => e.trim()).filter(e => e.includes("@"))
    const unique = Array.from(new Set(found))
    
    if(unique.length === 0) return alert("No valid emails found")

    setEmailList(unique.map(e => ({ email: e, checked: true })))
    setMode('REVIEW')
  }

  const handleFileUpload = async (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0]
    if (!file) return
    const text = await file.text()
    setRawInput(text) // Put text in box so user can see/edit before processing
  }

  const toggleEmail = (index: number) => {
    const newList = [...emailList]
    newList[index].checked = !newList[index].checked
    setEmailList(newList)
  }

  const handleSend = async () => {
    if (!user?.id) return alert("Login required")
    const finalEmails = emailList.filter(e => e.checked).map(e => e.email)
    
    setLoading(true)
    try {
        const res = await apiRequest("/invites/bulk", {
            method: "POST",
            body: JSON.stringify({ emails: finalEmails, issued_by: user.id })
        })
        setResult(res)
    } catch (e) {
        console.error(e)
        alert("Failed to send invites")
    } finally {
        setLoading(false)
    }
  }

  const reset = () => {
      setResult(null)
      setMode('INPUT')
      setRawInput("")
      setEmailList([])
  }

  return (
    <Dialog open={isOpen} onOpenChange={(val) => { setIsOpen(val); if(!val) reset(); }}>
      <DialogTrigger asChild>
        <Button className="gap-2"><Users className="w-4 h-4"/> Bulk Invite</Button>
      </DialogTrigger>
      <DialogContent className="sm:max-w-lg">
        <DialogHeader>
          <DialogTitle>Send Bulk Invitations</DialogTitle>
        </DialogHeader>
        
        <div className="space-y-4 py-4">
            
            {/* STEP 1: INPUT */}
            {!result && mode === 'INPUT' && (
                <div className="space-y-4">
                    <div className="border-2 border-dashed rounded-lg p-6 text-center hover:bg-muted/50 transition-colors cursor-pointer relative">
                        <input type="file" accept=".csv,.txt" onChange={handleFileUpload} className="absolute inset-0 opacity-0 cursor-pointer" />
                        <Upload className="w-8 h-8 mx-auto text-muted-foreground mb-2" />
                        <p className="text-sm font-medium">Drop CSV or click to upload</p>
                    </div>
                    
                    <Textarea 
                        placeholder="Paste emails here (comma or newline separated)..." 
                        value={rawInput}
                        onChange={e => setRawInput(e.target.value)}
                        rows={6}
                    />
                    
                    <Button onClick={handleProcess} disabled={!rawInput.trim()} className="w-full">
                        Process Emails
                    </Button>
                </div>
            )}

            {/* STEP 2: REVIEW LIST */}
            {!result && mode === 'REVIEW' && (
                <div className="space-y-4">
                    <div className="flex justify-between items-center">
                        <h3 className="text-sm font-medium">Select emails to invite:</h3>
                        <Button variant="ghost" size="sm" onClick={() => setMode('INPUT')}>Back to Edit</Button>
                    </div>
                    
                    <div className="border rounded-md max-h-60 overflow-y-auto p-2 space-y-1">
                        {emailList.map((item, i) => (
                            <div key={i} className="flex items-center gap-3 p-2 hover:bg-muted/50 rounded cursor-pointer" onClick={() => toggleEmail(i)}>
                                <div className={`w-4 h-4 border rounded flex items-center justify-center ${item.checked ? 'bg-black border-black text-white' : 'border-gray-400'}`}>
                                    {item.checked && <Check className="w-3 h-3"/>}
                                </div>
                                <span className="text-sm">{item.email}</span>
                            </div>
                        ))}
                    </div>

                    <Button onClick={handleSend} disabled={loading || emailList.filter(e=>e.checked).length === 0} className="w-full">
                        {loading ? <Loader2 className="w-4 h-4 animate-spin mr-2"/> : null}
                        Send {emailList.filter(e=>e.checked).length} Invites
                    </Button>
                </div>
            )}

            {/* STEP 3: RESULT */}
            {result && (
                <div className={`p-6 rounded-md text-center ${result.failed === 0 ? 'bg-green-50 text-green-700' : 'bg-orange-50 text-orange-700'}`}>
                    <div className="flex justify-center mb-4">
                        {result.failed === 0 ? <Check className="w-12 h-12"/> : <AlertCircle className="w-12 h-12"/>}
                    </div>
                    <h3 className="text-lg font-bold mb-2">
                        {result.success} Invites Sent
                    </h3>
                    {result.failed > 0 && <p className="text-sm">Failed: {result.failed}</p>}
                    
                    <Button variant="outline" onClick={reset} className="mt-6 w-full">Send More</Button>
                </div>
            )}
        </div>
      </DialogContent>
    </Dialog>
  )
}