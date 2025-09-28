"use client"

import { useState } from "react"
import { SidebarProvider, SidebarInset } from "@/components/ui/sidebar"
import { AppSidebar } from "./app-sidebar"
import { ChatInterface } from "@/components/chat/chat-interface"
import { PDFViewer } from "@/components/pdf/pdf-viewer"

export function MainLayout() {
  const [selectedPdfId, setSelectedPdfId] = useState<string | null>(null)
  const [isPdfViewerOpen, setIsPdfViewerOpen] = useState(false)
  

  return (
    <SidebarProvider defaultOpen={true}>
      <div className="flex min-h-screen w-full">
        <AppSidebar 
          onPdfSelect={setSelectedPdfId}
          selectedPdfId={selectedPdfId}
        />
        
        <SidebarInset className="flex-1">
          {/* Main Content */}
          <div className="flex overflow-hidden">
            {/* Chat Interface */}
            <div className={`flex-1 ${isPdfViewerOpen ? 'mr-2' : ''} transition-all duration-300`}>
              <ChatInterface 
                selectedPdfId={selectedPdfId}
                onShowPdf={(pdfId) => {
                  setSelectedPdfId(pdfId)
                  setIsPdfViewerOpen(true)
                }}
              />
            </div>
            
            {/* PDF Viewer Panel */}
            {isPdfViewerOpen && (
              <div className="border-l border-border bg-card w-[42%]">
                <PDFViewer 
                  pdfId={selectedPdfId}
                  onClose={() => setIsPdfViewerOpen(false)}
                />
              </div>
            )}
          </div>
        </SidebarInset>
      </div>
    </SidebarProvider>
  )
}
