"use client"

import { useState, useRef, useEffect } from "react"
import { MessageList } from "./message-list"
import AIMessageInput from "@/components/kokonutui/ai-input-search"
import { Card, CardContent } from "@/components/ui/card"
import { FileText } from "lucide-react"
import { chatService } from "@/lib/services/chat-service"
import { conversationManager } from "@/lib/services/conversation-manager"
import { pdfService } from "@/lib/services/pdf-service"
import { useApi } from "@/hooks/use-api"
import type { Conversation, Message } from "@/lib/types/conversation"

// Re-export Message type for backward compatibility
export type { Message }

interface ChatInterfaceProps {
  selectedPdfId: string | null
  currentConversation: Conversation | null
  onShowPdf: (pdfId: string) => void
  onConversationUpdate?: (conversation: Conversation) => void
  onNewConversation?: (conversation: Conversation) => void
}

export function ChatInterface({ 
  selectedPdfId, 
  currentConversation, 
  onShowPdf, 
  onConversationUpdate,
  onNewConversation 
}: ChatInterfaceProps) {
  const [messages, setMessages] = useState<Message[]>([])
  const [isLoading, setIsLoading] = useState(false)
  const messagesEndRef = useRef<HTMLDivElement>(null)

  const {
    data: pdfs = [],
    loading: isLoadingPdfs,
  } = useApi(pdfService.getDocuments, true)

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: "smooth" })
  }

  useEffect(() => {
    scrollToBottom()
  }, [messages])

  // Load conversation messages when conversation changes
  useEffect(() => {
    if (currentConversation) {
      setMessages(currentConversation.messages)
    } else {
      setMessages([])
    }
  }, [currentConversation])

  const handleFileSelect = (pdfId: string, pdfName: string) => {
    // Create draft conversation for selected file (not saved until first message)
    const conversation = conversationManager.createDraftConversation(pdfId, pdfName)
    onNewConversation?.(conversation)
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

  const handleSendMessage = async (content: string) => {
    if (!currentConversation) return

    const userMessage: Message = {
      id: Date.now().toString(),
      content,
      role: 'user',
      timestamp: new Date()
    }

    // Add user message to conversation (this will save conversation if it's the first message)
    const updatedConversation = conversationManager.addMessageToConversation(currentConversation, userMessage)
    setMessages(updatedConversation.messages)
    onConversationUpdate?.(updatedConversation)

    setIsLoading(true)

    try {
      // Use the real chat service
      const response = await chatService.sendMessage({
        message: content,
        documentIds: selectedPdfId ? [selectedPdfId] : undefined
      })

      const assistantMessage: Message = {
        id: response.message.id,
        content: response.message.content,
        role: 'assistant',
        timestamp: new Date(response.message.timestamp),
        sources: response.references?.map(ref => ({
          pdf_id: ref.documentId,
          filename: `Document ${ref.documentId}`,
          page: ref.pageNumber,
          content: ref.snippet,
          similarity_score: ref.relevanceScore
        })) || []
      }

      // Add assistant message to conversation
      const finalConversation = conversationManager.addMessageToConversation(updatedConversation, assistantMessage)
      setMessages(finalConversation.messages)
      onConversationUpdate?.(finalConversation)
    } catch {
      const errorMessage: Message = {
        id: (Date.now() + 1).toString(),
        content: "Sorry, I encountered an error while processing your request. Please try again.",
        role: 'assistant',
        timestamp: new Date()
      }
      
      // Add error message to conversation
      conversationManager.addMessage(currentConversation.id, errorMessage)
      const errorConversation = conversationManager.getConversation(currentConversation.id)
      if (errorConversation) {
        setMessages(errorConversation.messages)
        onConversationUpdate?.(errorConversation)
      }
    } finally {
      setIsLoading(false)
    }
  }

  // Removed unused clearChat and exportChat functions

  return (
    <div className="flex h-full flex-col w-full relative">
      {/* Main Chat Area */}
      <div className="flex-1 flex flex-col max-w-[52rem] mx-auto w-full min-h-0">
        {/* Messages Area - with internal scrolling */}
        <div className="flex-1 overflow-y-auto py-6 mb-24 w-full">
          {messages.length === 0 ? (
            <div className="flex flex-col items-center justify-center h-full text-center space-y-4">
              <div className="space-y-2">
                <h2 className="text-2xl font-semibold">How can I help you today?</h2>
                <p className="text-muted-foreground max-w-md">
                  {currentConversation 
                    ? "Ask me anything about your uploaded document. I'll provide answers based on the content."
                    : selectedPdfId
                    ? "Select a conversation or create a new one to start chatting with this document."
                    : "Upload a PDF document and create a conversation to start asking questions about it."
                  }
                </p>
              </div>
              {currentConversation && (
                <div className="flex items-center space-x-2 text-sm text-muted-foreground bg-muted/50 px-3 py-2 rounded-lg">
                  <div className="w-2 h-2 bg-green-500 rounded-full"></div>
                  <span>Conversation ready • {currentConversation.pdf_name}</span>
                </div>
              )}
            </div>
          ) : (
            <MessageList 
              messages={messages}
              isLoading={isLoading}
              onShowPdf={onShowPdf}
            />
          )}
          <div ref={messagesEndRef} />
        </div>

        {/* Input Area */}
        <div className="fixed bottom-0 m-2 space-y-2 bg-background/95 backdrop-blur-sm w-[52rem]">
          {!currentConversation && (
            <div className="space-y-2">
              <div className="text-center text-sm text-muted-foreground">
                Select a document to start chatting
              </div>
              
              {/* File List */}
              {isLoadingPdfs ? (
                <div className="text-center py-4">
                  <div className="text-sm text-muted-foreground">Loading documents...</div>
                </div>
              ) : pdfs && pdfs.length > 0 ? (
                <div className="space-y-1 max-h-32 overflow-y-auto">
                  {pdfs.map((pdf) => (
                    <Card
                      key={pdf.id}
                      className="cursor-pointer transition-colors hover:bg-accent/50 border-0 shadow-sm"
                      onClick={() => handleFileSelect(pdf.id, pdf.filename)}
                    >
                      <CardContent className="p-3">
                        <div className="flex items-center space-x-3">
                          <FileText className="h-4 w-4 text-blue-500 flex-shrink-0" />
                          <div className="flex-1 min-w-0">
                            <p className="text-sm font-medium truncate">
                              {pdf.filename}
                            </p>
                            <p className="text-xs text-muted-foreground">
                              {formatFileSize(pdf.fileSize)} • {formatDate(pdf.uploadDate)}
                            </p>
                          </div>
                        </div>
                      </CardContent>
                    </Card>
                  ))}
                </div>
              ) : (
                <div className="text-center py-4">
                  <FileText className="h-8 w-8 mx-auto mb-2 text-muted-foreground" />
                  <p className="text-sm text-muted-foreground">No documents uploaded yet</p>
                  <p className="text-xs text-muted-foreground">Upload a PDF to start chatting</p>
                </div>
              )}
            </div>
          )}
          
          <AIMessageInput 
            onSendMessage={handleSendMessage}
            disabled={isLoading || !currentConversation}
            placeholder={
              currentConversation
                ? `Ask a question about ${currentConversation.pdf_name}...`
                : "Select a document above to start chatting"
            }
          />
        </div>
      </div>
    </div>
  )
}
