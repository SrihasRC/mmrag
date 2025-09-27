"use client"

import { useState, useCallback } from "react"
import { Button } from "@/components/ui/button"
import { Card } from "@/components/ui/card"
import { Upload, X, Loader2 } from "lucide-react"
import { useDropzone } from "react-dropzone"

interface PDF {
  id: string
  filename: string
  status: 'processing' | 'completed' | 'error'
  uploadedAt: string
  size?: number
}

interface PDFUploadProps {
  onUploadComplete: (pdf: PDF) => void
}

export function PDFUpload({ onUploadComplete }: PDFUploadProps) {
  const [isUploading, setIsUploading] = useState(false)
  const [uploadProgress, setUploadProgress] = useState(0)
  const [error, setError] = useState<string | null>(null)

  const onDrop = useCallback(async (acceptedFiles: File[]) => {
    const file = acceptedFiles[0]
    if (!file) return

    // Validate file type
    if (file.type !== 'application/pdf') {
      setError('Please upload a PDF file')
      return
    }

    // Validate file size (max 50MB)
    if (file.size > 50 * 1024 * 1024) {
      setError('File size must be less than 50MB')
      return
    }

    setError(null)
    setIsUploading(true)
    setUploadProgress(0)

    try {
      // Simulate upload progress
      const progressInterval = setInterval(() => {
        setUploadProgress(prev => {
          if (prev >= 90) {
            clearInterval(progressInterval)
            return 90
          }
          return prev + 10
        })
      }, 200)

      // Create FormData for file upload
      const formData = new FormData()
      formData.append('file', file)

      // TODO: Replace with actual API call
      // const response = await fetch('/api/v1/rag/upload', {
      //   method: 'POST',
      //   body: formData,
      // })

      // Simulate API call
      await new Promise(resolve => setTimeout(resolve, 2000))
      
      clearInterval(progressInterval)
      setUploadProgress(100)

      // Mock successful response
      const newPdf: PDF = {
        id: Date.now().toString(),
        filename: file.name,
        status: 'processing',
        uploadedAt: new Date().toISOString(),
        size: file.size
      }

      onUploadComplete(newPdf)
      
      // Reset state
      setTimeout(() => {
        setIsUploading(false)
        setUploadProgress(0)
      }, 1000)

    } catch {
      setError('Upload failed. Please try again.')
      setIsUploading(false)
      setUploadProgress(0)
    }
  }, [onUploadComplete])

  const { getRootProps, getInputProps, isDragActive } = useDropzone({
    onDrop,
    accept: {
      'application/pdf': ['.pdf']
    },
    maxFiles: 1,
    disabled: isUploading
  })

  return (
    <div className="space-y-2">
      <Card
        {...getRootProps()}
        className={`
          relative cursor-pointer border-2 border-dashed p-6 text-center transition-colors
          ${isDragActive ? 'border-primary bg-primary/5' : 'border-muted-foreground/25'}
          ${isUploading ? 'cursor-not-allowed opacity-50' : 'hover:border-primary hover:bg-primary/5'}
        `}
      >
        <input {...getInputProps()} />
        
        {isUploading ? (
          <div className="space-y-2">
            <Loader2 className="mx-auto h-8 w-8 animate-spin text-primary" />
            <p className="text-sm text-muted-foreground">
              Uploading... {uploadProgress}%
            </p>
            <div className="mx-auto h-2 w-full max-w-xs overflow-hidden rounded-full bg-muted">
              <div 
                className="h-full bg-primary transition-all duration-300"
                style={{ width: `${uploadProgress}%` }}
              />
            </div>
          </div>
        ) : (
          <div className="space-y-2">
            <Upload className="mx-auto h-8 w-8 text-muted-foreground" />
            <div>
              <p className="text-sm font-medium">
                {isDragActive ? 'Drop your PDF here' : 'Upload PDF'}
              </p>
              <p className="text-xs text-muted-foreground">
                Drag & drop or click to select (max 50MB)
              </p>
            </div>
          </div>
        )}
      </Card>

      {error && (
        <div className="flex items-center gap-2 rounded-md bg-destructive/10 p-2 text-sm text-destructive">
          <X className="h-4 w-4" />
          <span>{error}</span>
          <Button
            variant="ghost"
            size="sm"
            onClick={() => setError(null)}
            className="ml-auto h-auto p-1"
          >
            <X className="h-3 w-3" />
          </Button>
        </div>
      )}
    </div>
  )
}
