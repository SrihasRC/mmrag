"use client"

import { useState, useEffect } from "react"
import dynamic from 'next/dynamic'
import { Button } from "@/components/ui/button"
import { Card } from "@/components/ui/card"
import { ScrollArea } from "@/components/ui/scroll-area"
import { Separator } from "@/components/ui/separator"
import { 
  X, 
  ZoomIn, 
  ZoomOut, 
  RotateCw, 
  Download, 
  ChevronLeft, 
  ChevronRight,
  FileText,
  Loader2
} from "lucide-react"

// Dynamically import react-pdf components to avoid SSR issues
const Document = dynamic(
  () => import('react-pdf').then((mod) => mod.Document),
  { ssr: false }
)

const Page = dynamic(
  () => import('react-pdf').then((mod) => mod.Page),
  { ssr: false }
)

// Configure PDF.js worker - use CDN for reliability
if (typeof window !== 'undefined') {
  import('react-pdf').then((reactPdf) => {
    // Use CDN worker for better compatibility
    reactPdf.pdfjs.GlobalWorkerOptions.workerSrc = `//unpkg.com/pdfjs-dist@${reactPdf.pdfjs.version}/build/pdf.worker.min.js`
  }).catch(() => {
    // Fallback if the above fails
    import('react-pdf').then((reactPdf) => {
      reactPdf.pdfjs.GlobalWorkerOptions.workerSrc = `//unpkg.com/pdfjs-dist@${reactPdf.pdfjs.version}/legacy/build/pdf.worker.min.js`
    })
  })
}

interface PDFViewerProps {
  pdfId: string | null
  onClose: () => void
}

export function PDFViewer({ pdfId, onClose }: PDFViewerProps) {
  const [currentPage, setCurrentPage] = useState(1)
  const [zoom, setZoom] = useState(100)
  const [rotation, setRotation] = useState(0)
  const [numPages, setNumPages] = useState<number>(0)
  const [isLoading, setIsLoading] = useState(true)
  const [pdfFile, setPdfFile] = useState<string | null>(null)
  const [pdfTitle, setPdfTitle] = useState<string>("")
  
  // Mock PDF URL - in real implementation, this would come from API
  useEffect(() => {
    if (pdfId) {
      setIsLoading(true)
      // Simulate API call to get PDF data
      setTimeout(() => {
        // For demo, we'll use a public PDF URL
        setPdfFile("https://mozilla.github.io/pdf.js/web/compressed.tracemonkey-pldi-09.pdf")
        setPdfTitle("Sample Research Paper.pdf")
        setIsLoading(false)
      }, 1000)
    }
  }, [pdfId])

  const onDocumentLoadSuccess = ({ numPages }: { numPages: number }) => {
    setNumPages(numPages)
    setCurrentPage(1)
    setIsLoading(false)
  }

  const onDocumentLoadError = (error: Error) => {
    console.error('Error loading PDF:', error)
    setIsLoading(false)
  }

  const handleZoomIn = () => {
    setZoom(prev => Math.min(prev + 25, 200))
  }

  const handleZoomOut = () => {
    setZoom(prev => Math.max(prev - 25, 50))
  }

  const handleRotate = () => {
    setRotation(prev => (prev + 90) % 360)
  }

  const handlePrevPage = () => {
    setCurrentPage(prev => Math.max(prev - 1, 1))
  }

  const handleNextPage = () => {
    setCurrentPage(prev => Math.min(prev + 1, numPages))
  }

  if (!pdfId) {
    return (
      <div className="flex h-full items-center justify-center p-8">
        <div className="text-center">
          <FileText className="mx-auto h-12 w-12 text-muted-foreground mb-4" />
          <p className="text-sm text-muted-foreground">
            Select a document to view it here
          </p>
        </div>
      </div>
    )
  }

  return (
    <div className="flex h-full flex-col">
      {/* Header */}
      <div className="flex items-center justify-between border-b border-border p-4">
        <div className="flex-1 min-w-0">
          <h3 className="font-semibold text-sm truncate">{pdfTitle}</h3>
          <p className="text-xs text-muted-foreground">
            Page {currentPage} of {numPages}
          </p>
        </div>
        
        <Button
          variant="ghost"
          size="sm"
          onClick={onClose}
          className="ml-2"
        >
          <X className="h-4 w-4" />
        </Button>
      </div>

      {/* Toolbar */}
      <div className="flex items-center gap-1 border-b border-border p-2">
        <div className="flex items-center gap-1">
          <Button
            variant="ghost"
            size="sm"
            onClick={handlePrevPage}
            disabled={currentPage === 1}
          >
            <ChevronLeft className="h-4 w-4" />
          </Button>
          
          <span className="text-xs text-muted-foreground px-2">
            {currentPage} / {numPages}
          </span>
          
          <Button
            variant="ghost"
            size="sm"
            onClick={handleNextPage}
            disabled={currentPage === numPages}
          >
            <ChevronRight className="h-4 w-4" />
          </Button>
        </div>

        <Separator orientation="vertical" className="h-6 mx-2" />

        <div className="flex items-center gap-1">
          <Button
            variant="ghost"
            size="sm"
            onClick={handleZoomOut}
            disabled={zoom === 50}
          >
            <ZoomOut className="h-4 w-4" />
          </Button>
          
          <span className="text-xs text-muted-foreground px-2 min-w-[3rem] text-center">
            {zoom}%
          </span>
          
          <Button
            variant="ghost"
            size="sm"
            onClick={handleZoomIn}
            disabled={zoom === 200}
          >
            <ZoomIn className="h-4 w-4" />
          </Button>
        </div>

        <Separator orientation="vertical" className="h-6 mx-2" />

        <Button
          variant="ghost"
          size="sm"
          onClick={handleRotate}
        >
          <RotateCw className="h-4 w-4" />
        </Button>

        <Button
          variant="ghost"
          size="sm"
        >
          <Download className="h-4 w-4" />
        </Button>
      </div>

      {/* PDF Content */}
      <ScrollArea className="flex-1">
        <div className="p-4">
          <Card className="mx-auto max-w-fit">
            {isLoading ? (
              <div className="flex h-96 w-96 items-center justify-center">
                <div className="text-center">
                  <Loader2 className="mx-auto h-8 w-8 animate-spin mb-4" />
                  <p className="text-sm text-muted-foreground">Loading PDF...</p>
                </div>
              </div>
            ) : pdfFile ? (
              <Document
                file={pdfFile}
                onLoadSuccess={onDocumentLoadSuccess}
                onLoadError={onDocumentLoadError}
                loading={
                  <div className="flex h-96 w-96 items-center justify-center">
                    <Loader2 className="h-8 w-8 animate-spin" />
                  </div>
                }
                error={
                  <div className="flex h-96 w-96 items-center justify-center">
                    <div className="text-center">
                      <FileText className="mx-auto h-16 w-16 text-red-400 mb-4" />
                      <p className="text-sm text-red-600">Failed to load PDF</p>
                    </div>
                  </div>
                }
              >
                <div
                  style={{
                    transform: `rotate(${rotation}deg)`,
                    transformOrigin: 'center center'
                  }}
                >
                  <Page
                    pageNumber={currentPage}
                    scale={zoom / 100}
                    renderTextLayer={true}
                    renderAnnotationLayer={true}
                  />
                </div>
              </Document>
            ) : (
              <div className="flex h-96 w-96 items-center justify-center">
                <div className="text-center">
                  <FileText className="mx-auto h-16 w-16 text-gray-400 mb-4" />
                  <p className="text-sm text-gray-600">No PDF selected</p>
                </div>
              </div>
            )}
          </Card>
        </div>
      </ScrollArea>

      {/* Reference Highlights (when available) */}
      <div className="border-t border-border p-4">
        <h4 className="text-sm font-medium mb-2">References on this page</h4>
        <div className="space-y-2">
          <Card className="p-3 bg-primary/5 border-primary/20">
            <p className="text-xs text-muted-foreground">
              &quot;This section discusses the methodology used in the research...&quot;
            </p>
            <div className="flex items-center justify-between mt-2">
              <span className="text-xs font-medium">95% relevance</span>
              <Button variant="ghost" size="sm" className="h-6 text-xs">
                Highlight
              </Button>
            </div>
          </Card>
        </div>
      </div>
    </div>
  )
}
