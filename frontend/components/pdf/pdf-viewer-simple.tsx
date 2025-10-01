"use client"

import { useState, useEffect } from "react"
import { Button } from "@/components/ui/button"
import { 
  X, 
  Download, 
  FileText,
  Loader2
} from "lucide-react"

interface PDFViewerProps {
  pdfId: string | null
  onClose: () => void
}

export function PDFViewer({ pdfId, onClose }: PDFViewerProps) {
  const [isLoading, setIsLoading] = useState(true)
  const [pdfFile, setPdfFile] = useState<string | null>(null)
  const [pdfTitle, setPdfTitle] = useState<string>("")
  const [error, setError] = useState<string | null>(null)

  useEffect(() => {
    if (pdfId) {
      setIsLoading(true)
      setError(null)
      
      try {
        // Get real PDF URL from backend
        const pdfUrl = `http://localhost:8000/api/v1/rag/pdf/${pdfId}/file`
        setPdfFile(pdfUrl)
        
        // Set a simple title and finish loading
        setPdfTitle(`Document ${pdfId.slice(0, 8)}.pdf`)
        setIsLoading(false)
        
      } catch (urlError) {
        console.error('Error getting PDF URL:', urlError)
        setError('Failed to load PDF')
        setIsLoading(false)
      }
    }
  }, [pdfId])

  const handleDownload = () => {
    if (pdfFile) {
      const link = document.createElement('a')
      link.href = pdfFile
      link.download = pdfTitle
      document.body.appendChild(link)
      link.click()
      document.body.removeChild(link)
    }
  }

  if (!pdfId) return null

  return (
    <div className="h-full flex flex-col">
      {/* Header */}
      <div className="flex items-center justify-between p-3 border-b bg-background/95 backdrop-blur supports-[backdrop-filter]:bg-background/60">
        <div className="flex items-center space-x-2 min-w-0">
          <FileText className="h-4 w-4 text-blue-600 flex-shrink-0" />
          <h2 className="font-medium text-sm truncate" title={pdfTitle}>
            {pdfTitle}
          </h2>
        </div>
        <div className="flex items-center space-x-1 flex-shrink-0">
          <Button
            variant="ghost"
            size="sm"
            onClick={handleDownload}
            disabled={!pdfFile}
            className="h-7 w-7 p-0"
          >
            <Download className="h-3 w-3" />
          </Button>
          <Button 
            variant="ghost" 
            size="sm" 
            onClick={onClose}
            className="h-7 w-7 p-0"
          >
            <X className="h-3 w-3" />
          </Button>
        </div>
      </div>



      {/* PDF Content */}
      <div className="flex-1 relative overflow-hidden">
        {isLoading ? (
          <div className="flex h-full items-center justify-center">
            <div className="text-center">
              <Loader2 className="mx-auto h-8 w-8 animate-spin mb-4" />
              <p className="text-sm text-muted-foreground">Loading PDF...</p>
            </div>
          </div>
        ) : error ? (
          <div className="flex h-full items-center justify-center">
            <div className="text-center">
              <FileText className="mx-auto h-16 w-16 text-red-400 mb-4" />
              <p className="text-sm text-red-600">{error}</p>
            </div>
          </div>
        ) : pdfFile ? (
          <iframe
            src={pdfFile}
            className="w-full h-full border-0"
            title={pdfTitle}
            onLoad={() => setIsLoading(false)}
            onError={() => {
              setError('Failed to load PDF')
              setIsLoading(false)
            }}
          />
        ) : (
          <div className="flex h-full items-center justify-center">
            <div className="text-center">
              <FileText className="mx-auto h-16 w-16 text-gray-400 mb-4" />
              <p className="text-sm text-muted-foreground">No PDF selected</p>
            </div>
          </div>
        )}
      </div>
    </div>
  )
}