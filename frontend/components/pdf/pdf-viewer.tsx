"use client"

import { useState } from "react"
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
  FileText
} from "lucide-react"

interface PDFViewerProps {
  pdfId: string | null
  onClose: () => void
}

export function PDFViewer({ pdfId, onClose }: PDFViewerProps) {
  const [currentPage, setCurrentPage] = useState(1)
  const [zoom, setZoom] = useState(100)
  const [rotation, setRotation] = useState(0)
  
  // Mock data - in real implementation, this would come from API
  const totalPages = 10
  const pdfTitle = "Research Paper.pdf"

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
    setCurrentPage(prev => Math.min(prev + 1, totalPages))
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
            Page {currentPage} of {totalPages}
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
            {currentPage} / {totalPages}
          </span>
          
          <Button
            variant="ghost"
            size="sm"
            onClick={handleNextPage}
            disabled={currentPage === totalPages}
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
            {/* Placeholder for PDF content */}
            <div 
              className="bg-white border border-border shadow-sm"
              style={{
                width: `${(595 * zoom) / 100}px`,
                height: `${(842 * zoom) / 100}px`,
                transform: `rotate(${rotation}deg)`,
                transformOrigin: 'center center'
              }}
            >
              <div className="flex h-full items-center justify-center text-gray-400">
                <div className="text-center">
                  <FileText className="mx-auto h-16 w-16 mb-4" />
                  <p className="text-sm">PDF Page {currentPage}</p>
                  <p className="text-xs mt-2">
                    In a real implementation, this would show the actual PDF content
                  </p>
                </div>
              </div>
            </div>
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
