"use client"

import { useState, useRef, useEffect } from "react"
import { MessageList } from "./message-list"
import AIMessageInput from "@/components/kokonutui/ai-input-search"
import { chatService } from "@/lib/services/chat-service"

export interface Message {
  id: string
  content: string
  role: 'user' | 'assistant'
  timestamp: Date
  sources?: Array<{
    pdf_id: string
    filename: string
    page: number
    content: string
    similarity_score: number
  }>
  isStreaming?: boolean
}

interface ChatInterfaceProps {
  selectedPdfId: string | null
  onShowPdf: (pdfId: string) => void
}

export function ChatInterface({ selectedPdfId, onShowPdf }: ChatInterfaceProps) {
  const [messages, setMessages] = useState<Message[]>([])
  const [isLoading, setIsLoading] = useState(false)
  const messagesEndRef = useRef<HTMLDivElement>(null)

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: "smooth" })
  }

  useEffect(() => {
    scrollToBottom()
  }, [messages])

  const handleSendMessage = async (content: string) => {
    const userMessage: Message = {
      id: Date.now().toString(),
      content,
      role: 'user',
      timestamp: new Date()
    }

    setMessages(prev => [...prev, userMessage])
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

      setMessages(prev => [...prev, assistantMessage])
    } catch {
      const errorMessage: Message = {
        id: (Date.now() + 1).toString(),
        content: "Sorry, I encountered an error while processing your request. Please try again.",
        role: 'assistant',
        timestamp: new Date()
      }
      setMessages(prev => [...prev, errorMessage])
    } finally {
      setIsLoading(false)
    }
  }

  // Removed unused clearChat and exportChat functions

  return (
    <div className="flex h-screen overflow-auto flex-col bg-background w-full">
      {/* Main Chat Area */}
      <div className="flex-1 flex flex-col max-w-[52rem] mx-auto w-full">
        {/* Messages Area */}
        <div className="flex-1 overflow-hidden py-6 w-full">
          {messages.length === 0 ? (
            <div className="flex flex-col items-center justify-center h-full text-center space-y-4">
              <div className="space-y-2">
                <h2 className="text-2xl font-semibold">How can I help you today?</h2>
                <p className="text-muted-foreground max-w-md">
                  {selectedPdfId 
                    ? "Ask me anything about your uploaded document. I'll provide answers based on the content."
                    : "Upload a PDF document to start asking questions about it."
                  }
                </p>
              </div>
              {selectedPdfId && (
                <div className="flex items-center space-x-2 text-sm text-muted-foreground bg-muted/50 px-3 py-2 rounded-lg">
                  <div className="w-2 h-2 bg-green-500 rounded-full"></div>
                  <span>Document ready for questions</span>
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
        <div className="sticky bottom-0 p-2">
            <AIMessageInput 
              onSendMessage={handleSendMessage}
              disabled={isLoading}
              placeholder={
                selectedPdfId 
                  ? "Ask a question about your document..." 
                  : "Upload a document to start chatting..."
              }
            />
        </div>
      </div>
    </div>
  )
}
