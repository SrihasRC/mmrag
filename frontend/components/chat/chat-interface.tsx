"use client"

import { useState, useRef, useEffect } from "react"
import { MessageList } from "./message-list"
import { MessageInput } from "./message-input"
import { Card } from "@/components/ui/card"
import { Button } from "@/components/ui/button"
import { Trash2, Download } from "lucide-react"

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
      // TODO: Replace with actual API call
      // const response = await fetch('/api/v1/rag/query', {
      //   method: 'POST',
      //   headers: { 'Content-Type': 'application/json' },
      //   body: JSON.stringify({
      //     question: content,
      //     pdf_id: selectedPdfId,
      //     top_k: 5
      //   })
      // })

      // Simulate API response
      await new Promise(resolve => setTimeout(resolve, 1500))

      const assistantMessage: Message = {
        id: (Date.now() + 1).toString(),
        content: `This is a simulated response to your question: "${content}". In a real implementation, this would be the AI-generated answer based on your uploaded PDFs.`,
        role: 'assistant',
        timestamp: new Date(),
        sources: selectedPdfId ? [
          {
            pdf_id: selectedPdfId,
            filename: "Research Paper.pdf",
            page: 1,
            content: "This is a sample reference from the PDF that was used to generate the answer...",
            similarity_score: 0.95
          },
          {
            pdf_id: selectedPdfId,
            filename: "Research Paper.pdf", 
            page: 3,
            content: "Another relevant section from the document that supports the answer...",
            similarity_score: 0.87
          }
        ] : undefined
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

  const clearChat = () => {
    setMessages([])
  }

  const exportChat = () => {
    const chatData = {
      messages,
      exportedAt: new Date().toISOString(),
      selectedPdf: selectedPdfId
    }
    
    const blob = new Blob([JSON.stringify(chatData, null, 2)], {
      type: 'application/json'
    })
    
    const url = URL.createObjectURL(blob)
    const a = document.createElement('a')
    a.href = url
    a.download = `chat-export-${new Date().toISOString().split('T')[0]}.json`
    document.body.appendChild(a)
    a.click()
    document.body.removeChild(a)
    URL.revokeObjectURL(url)
  }

  return (
    <div className="flex h-full flex-col bg-background">
      {/* Chat Header */}
      <div className="flex items-center justify-between border-b border-border bg-card px-4 py-3">
        <div>
          <h2 className="font-semibold text-card-foreground">
            Chat Assistant
          </h2>
          {selectedPdfId && (
            <p className="text-sm text-muted-foreground">
              Context: Research Paper.pdf
            </p>
          )}
        </div>
        
        <div className="flex items-center gap-2">
          <Button
            variant="ghost"
            size="sm"
            onClick={exportChat}
            disabled={messages.length === 0}
          >
            <Download className="h-4 w-4 mr-2" />
            Export
          </Button>
          <Button
            variant="ghost"
            size="sm"
            onClick={clearChat}
            disabled={messages.length === 0}
          >
            <Trash2 className="h-4 w-4 mr-2" />
            Clear
          </Button>
        </div>
      </div>

      {/* Messages Area */}
      <div className="flex-1 overflow-hidden">
        {messages.length === 0 ? (
          <div className="flex h-full items-center justify-center">
            <Card className="max-w-md p-6 text-center">
              <h3 className="mb-2 text-lg font-semibold">Welcome to MMRAG Assistant</h3>
              <p className="text-sm text-muted-foreground mb-4">
                Upload a PDF document and start asking questions about its content. 
                I&apos;ll help you find relevant information and provide detailed answers.
              </p>
              <div className="space-y-2 text-xs text-muted-foreground">
                <p>• Upload PDFs using the sidebar</p>
                <p>• Ask questions about the content</p>
                <p>• View source references in the PDF viewer</p>
              </div>
            </Card>
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

      {/* Message Input */}
      <div className="border-t border-border bg-card p-4">
        <MessageInput 
          onSendMessage={handleSendMessage}
          disabled={isLoading}
          placeholder={
            selectedPdfId 
              ? "Ask a question about your document..." 
              : "Upload a PDF first, then ask questions about it..."
          }
        />
      </div>
    </div>
  )
}
