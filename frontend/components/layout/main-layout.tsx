"use client"

import { useState } from "react"
import { SidebarProvider, SidebarInset } from "@/components/ui/sidebar"
import { AppSidebar } from "./app-sidebar"
import { ChatInterface } from "@/components/chat/chat-interface"
import { PDFViewer } from "@/components/pdf/pdf-viewer-simple"

import type { Conversation } from "@/lib/types/conversation"

export function MainLayout() {
  const [selectedPdfId, setSelectedPdfId] = useState<string | null>(null)
  const [currentConversation, setCurrentConversation] = useState<Conversation | null>(null)
  const [isPdfViewerOpen, setIsPdfViewerOpen] = useState(false)

  const handleConversationSelect = (conversation: Conversation) => {
    setCurrentConversation(conversation)
    setSelectedPdfId(conversation.pdf_id)
  }

  const handleNewConversation = (conversation: Conversation) => {
    setCurrentConversation(conversation)
    setSelectedPdfId(conversation.pdf_id)
  }

  const handleNewChat = () => {
    // Clear current conversation to show file selection
    setCurrentConversation(null)
    setSelectedPdfId(null)
  }

  const handleConversationUpdate = (conversation: Conversation) => {
    // Update the current conversation with latest data
    setCurrentConversation(conversation)
  }
  

  return (
    <SidebarProvider>
      <AppSidebar 
        currentConversation={currentConversation}
        onConversationSelect={handleConversationSelect}
        onNewChat={handleNewChat}
      />
      <SidebarInset>
        <div className="flex-1 overflow-hidden">
          <div className="flex h-full">
            {/* Chat Interface - Main */}
            <div className="flex-1 flex flex-col">
              <ChatInterface
                selectedPdfId={selectedPdfId}
                currentConversation={currentConversation}
                onShowPdf={(pdfId: string) => {
                  setSelectedPdfId(pdfId)
                  setIsPdfViewerOpen(true)
                }}
                onConversationUpdate={handleConversationUpdate}
                onNewConversation={handleNewConversation}
              />
            </div>
            
            {/* PDF Viewer - Right Panel */}
            {isPdfViewerOpen && (
              <div className="w-1/2 border-l">
                <PDFViewer 
                  pdfId={selectedPdfId} 
                  onClose={() => setIsPdfViewerOpen(false)}
                />
              </div>
            )}
          </div>
        </div>
      </SidebarInset>
    </SidebarProvider>
  )
}