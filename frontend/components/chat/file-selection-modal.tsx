"use client"

import { useState } from "react"
import { Button } from "@/components/ui/button"
import { Card, CardContent } from "@/components/ui/card"
import { Badge } from "@/components/ui/badge"
import { ScrollArea } from "@/components/ui/scroll-area"
import { FileText, Loader2, X } from "lucide-react"
import { pdfService } from "@/lib/services/pdf-service"
import { useApi } from "@/hooks/use-api"

interface FileSelectionModalProps {
  isOpen: boolean
  onClose: () => void
  onFileSelect: (pdfId: string, pdfName: string) => void
}

export function FileSelectionModal({ isOpen, onClose, onFileSelect }: FileSelectionModalProps) {
  const [selectedPdfId, setSelectedPdfId] = useState<string>("")

  const {
    data: pdfs = [],
    loading: isLoadingPdfs,
  } = useApi(pdfService.getDocuments, true)

  const handleFileSelect = (pdfId: string) => {
    setSelectedPdfId(pdfId)
  }

  const handleConfirm = () => {
    const selectedPdf = pdfs?.find(pdf => pdf.id === selectedPdfId)
    if (selectedPdf) {
      onFileSelect(selectedPdf.id, selectedPdf.filename)
      handleClose()
    }
  }

  const handleClose = () => {
    onClose()
    setSelectedPdfId("")
  }

  const formatFileSize = (bytes: number) => {
    if (bytes === 0) return '0 Bytes'
    const k = 1024
    const sizes = ['Bytes', 'KB', 'MB', 'GB']
    const i = Math.floor(Math.log(bytes) / Math.log(k))
    return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i]
  }

  const formatDate = (dateString: string) => {
    return new Date(dateString).toLocaleDateString('en-US', {
      month: 'short',
      day: 'numeric',
      year: 'numeric'
    })
  }

  if (!isOpen) return null

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center">
      {/* Backdrop */}
      <div 
        className="absolute inset-0 bg-black/50 backdrop-blur-sm"
        onClick={handleClose}
      />
      
      {/* Modal */}
      <div className="relative bg-background border rounded-lg shadow-lg w-full max-w-2xl mx-4 max-h-[80vh] flex flex-col">
        {/* Header */}
        <div className="flex items-center justify-between p-6 border-b">
          <div>
            <h2 className="text-lg font-semibold">Select a Document</h2>
            <p className="text-sm text-muted-foreground">Choose a PDF document to start chatting</p>
          </div>
          <Button
            variant="ghost"
            size="sm"
            onClick={handleClose}
            className="h-8 w-8 p-0"
          >
            <X className="h-4 w-4" />
          </Button>
        </div>

        {/* Content */}
        <div className="flex-1 overflow-y-scroll">
          {isLoadingPdfs ? (
            <div className="flex items-center justify-center py-12">
              <Loader2 className="h-6 w-6 animate-spin mr-2" />
              <span className="text-sm text-muted-foreground">Loading documents...</span>
            </div>
          ) : pdfs && pdfs.length > 0 ? (
            <ScrollArea className="h-full">
              <div className="p-6 pt-4 space-y-3">
                {pdfs.map((pdf) => (
                  <Card
                    key={pdf.id}
                    className={`cursor-pointer transition-all hover:bg-accent/50 py-0 ${
                      selectedPdfId === pdf.id 
                        ? 'border-primary bg-accent/30 ring-1 ring-primary/20' 
                        : 'border-border hover:border-accent-foreground/20'
                    }`}
                    onClick={() => handleFileSelect(pdf.id)}
                  >
                    <CardContent className="p-4">
                      <div className="flex items-center space-x-4">
                        <div className="flex-shrink-0">
                          <FileText className="h-10 w-10 text-blue-500" />
                        </div>
                        
                        <div className="flex-1 min-w-0 space-y-2">
                          <div className="flex items-center justify-between">
                            <h3 className="text-sm font-medium truncate pr-2">
                              {pdf.filename}
                            </h3>
                            {pdf.status === 'processing' && (
                              <Badge variant="secondary" className="text-xs">
                                Processing
                              </Badge>
                            )}
                          </div>
                          
                          <div className="flex items-center text-xs text-muted-foreground space-x-4">
                            <span>{formatFileSize(pdf.fileSize)}</span>
                            <span>•</span>
                            <span>Uploaded {formatDate(pdf.uploadDate)}</span>
                          </div>
                        </div>
                      </div>
                    </CardContent>
                  </Card>
                ))}
              </div>
            </ScrollArea>
          ) : (
            <div className="flex flex-col items-center justify-center py-12 px-6 text-center">
              <FileText className="h-16 w-16 text-muted-foreground mb-4" />
              <h3 className="text-lg font-medium mb-2">No documents uploaded yet</h3>
              <p className="text-sm text-muted-foreground max-w-sm">
                Upload a PDF document first to start chatting with your documents.
              </p>
            </div>
          )}
        </div>

        {/* Footer */}
        {pdfs && pdfs.length > 0 && (
          <div className="flex items-center justify-between p-6 border-t bg-muted/20">
            <div className="text-sm text-muted-foreground">
              {selectedPdfId ? "Document selected" : "Select a document to continue"}
            </div>
            <div className="flex space-x-3">
              <Button variant="outline" onClick={handleClose}>
                Cancel
              </Button>
              <Button 
                onClick={handleConfirm}
                disabled={!selectedPdfId || isLoadingPdfs}
              >
                Start Chat
              </Button>
            </div>
          </div>
        )}
      </div>
    </div>
  )
}
