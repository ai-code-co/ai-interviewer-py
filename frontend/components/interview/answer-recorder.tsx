"use client"
import { useEffect, useRef } from "react"
import { Button } from "@/components/ui/button"
import { ArrowRight, Loader2 } from "lucide-react"

interface Props {
  stream: MediaStream | null
  onSubmit?: () => void
  isLoading?: boolean // NEW PROP
  isReadOnly?: boolean
  subtitle?: string
}

export function InterviewAnswerRecorder({ stream, onSubmit, isLoading = false, isReadOnly = false, subtitle }: Props) {
  const videoRef = useRef<HTMLVideoElement | null>(null)

  useEffect(() => {
    if (videoRef.current && stream) {
      videoRef.current.srcObject = stream
    }
  }, [stream])

  return (
    <div className="relative w-full h-full">
      {/* Video Feed */}
      <video 
        ref={videoRef} 
        autoPlay 
        muted 
        playsInline 
        className="w-full h-full object-cover transform scale-x-[-1]" 
      />
      
      {!isReadOnly && (
        <>
            {/* Gradient Overlay */}
            <div className="absolute bottom-0 left-0 right-0 h-40 bg-gradient-to-t from-black/90 via-black/40 to-transparent pointer-events-none" />

            {/* Controls Container */}
            <div className="absolute bottom-6 left-0 right-0 flex flex-col items-center gap-6 px-4 z-10">
            
            {/* SUBTITLE BUBBLE */}
            {subtitle && (
                <div className="px-6 py-3 bg-black/60 text-white/95 text-base font-medium rounded-2xl backdrop-blur-md max-w-2xl text-center shadow-lg border border-white/10 animate-in fade-in slide-in-from-bottom-2">
                    {subtitle}
                </div>
            )}

            {/* Next Button with Loading State */}
            <Button 
                onClick={onSubmit} 
                disabled={isLoading} // Disable while processing
                className="rounded-full px-10 h-14 text-base font-semibold bg-white text-black hover:bg-neutral-200 shadow-xl hover:scale-105 transition-all disabled:opacity-70 disabled:scale-100 disabled:cursor-wait"
            >
                {isLoading ? (
                    <>
                        <Loader2 className="w-5 h-5 mr-2 animate-spin" /> Processing...
                    </>
                ) : (
                    <>
                        Next Question <ArrowRight className="w-5 h-5 ml-2"/>
                    </>
                )}
            </Button>
            </div>
        </>
      )}
      
      {/* REC Indicator */}
      <div className="absolute top-4 right-4 flex items-center gap-2 bg-black/40 backdrop-blur-sm border border-white/10 text-white px-3 py-1 rounded-full text-[10px] font-bold tracking-wider">
        <div className="w-1.5 h-1.5 bg-red-500 rounded-full animate-pulse"/> REC
      </div>
    </div>
  )
}