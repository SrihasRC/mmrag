"use client"

import { useState, useEffect } from "react"
import { Button } from "@/components/ui/button"
import { Card } from "@/components/ui/card"
import { Badge } from "@/components/ui/badge"
import { 
  MessageCircle, 
  Plus, 
  Trash2, 
  Clock,
  FileText,
  MoreHorizontal
} from "lucide-react"
import { conversationManager } from "@/lib/services/conversation-manager"
import type { Conversation, ConversationSummary } from "@/lib/types/conversation"
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuTrigger,
} from "@/components/ui/dropdown-menu"

interface ConversationListProps {
  selectedPdfId: string | null
  selectedPdfName?: string
  currentConversation: Conversation | null
  onConversationSelect: (conversation: Conversation) => void
  onNewConversation: () => void
}

export function ConversationList({
  selectedPdfId,
  selectedPdfName,
  currentConversation,
  onConversationSelect,
  onNewConversation
}: ConversationListProps) {
  const [conversations, setConversations] = useState<ConversationSummary[]>([])
  const [pdfConversations, setPdfConversations] = useState<ConversationSummary[]>([])
  
  useEffect(() => {
    loadConversations()
  }, [])

  useEffect(() => {
    if (selectedPdfId) {
      const filtered = conversations.filter(c => c.pdf_id === selectedPdfId)
      setPdfConversations(filtered)
    } else {
      setPdfConversations([])
    }
  }, [selectedPdfId, conversations])

  const loadConversations = () => {
    const allConversations = conversationManager.getAllConversations()
    setConversations(allConversations)
  }

  const handleDeleteConversation = (conversationId: string) => {
    conversationManager.deleteConversation(conversationId)
    loadConversations()
    
    // If we deleted the current conversation, clear selection
    if (currentConversation?.id === conversationId) {
      // This would need to be handled by parent component
    }
  }

  const handleConversationClick = (conversationSummary: ConversationSummary) => {
    const fullConversation = conversationManager.getConversation(conversationSummary.id)
    if (fullConversation) {
      onConversationSelect(fullConversation)
    }
  }

  const formatDate = (dateString: string) => {
    const date = new Date(dateString)
    const now = new Date()
    const diffMs = now.getTime() - date.getTime()
    const diffDays = Math.floor(diffMs / (1000 * 60 * 60 * 24))
    
    if (diffDays === 0) {
      return date.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })
    } else if (diffDays === 1) {
      return 'Yesterday'
    } else if (diffDays < 7) {
      return `${diffDays} days ago`
    } else {
      return date.toLocaleDateString()
    }
  }

  if (!selectedPdfId) {
    return (
      <div className="p-4 text-center text-muted-foreground">
        <FileText className="mx-auto h-12 w-12 mb-4 opacity-50" />
        <p className="text-sm">Select a document to view conversations</p>
      </div>
    )
  }

  return (
    <div className="flex flex-col h-full">
      {/* Header */}
      <div className="p-4 border-b">
        <div className="flex items-center justify-between mb-2">
          <h3 className="font-semibold text-sm">Conversations</h3>
          <Button
            variant="ghost"
            size="sm"
            onClick={onNewConversation}
            className="h-8 w-8 p-0"
            title="New conversation"
          >
            <Plus className="h-4 w-4" />
          </Button>
        </div>
        {selectedPdfName && (
          <p className="text-xs text-muted-foreground truncate" title={selectedPdfName}>
            {selectedPdfName}
          </p>
        )}
      </div>

      {/* Conversations List */}
      <div className="flex-1 overflow-y-auto">
        {pdfConversations.length === 0 ? (
          <div className="p-4 text-center">
            <MessageCircle className="mx-auto h-8 w-8 mb-2 opacity-50" />
            <p className="text-sm text-muted-foreground mb-3">No conversations yet</p>
            <Button 
              variant="outline" 
              size="sm" 
              onClick={onNewConversation}
              className="w-full"
            >
              <Plus className="h-4 w-4 mr-2" />
              Start New Chat
            </Button>
          </div>
        ) : (
          <div className="p-2 space-y-2">
            {pdfConversations.map((conv) => (
              <Card
                key={conv.id}
                className={`p-3 cursor-pointer transition-colors hover:bg-muted/50 ${
                  currentConversation?.id === conv.id 
                    ? 'bg-muted border-primary/50' 
                    : 'bg-card'
                }`}
                onClick={() => handleConversationClick(conv)}
              >
                <div className="flex items-start justify-between gap-2">
                  <div className="flex-1 min-w-0">
                    <div className="flex items-center gap-2 mb-1">
                      <h4 className="font-medium text-sm truncate">
                        {conv.title}
                      </h4>
                      {conv.message_count > 0 && (
                        <Badge variant="secondary" className="text-xs px-1">
                          {conv.message_count}
                        </Badge>
                      )}
                    </div>
                    
                    {conv.last_message && (
                      <p className="text-xs text-muted-foreground line-clamp-2 mb-2">
                        {conv.last_message}
                      </p>
                    )}
                    
                    <div className="flex items-center gap-1 text-xs text-muted-foreground">
                      <Clock className="h-3 w-3" />
                      <span>{formatDate(conv.updated_at)}</span>
                    </div>
                  </div>
                  
                  <DropdownMenu>
                    <DropdownMenuTrigger asChild>
                      <Button
                        variant="ghost"
                        size="sm"
                        className="h-6 w-6 p-0 opacity-0 group-hover:opacity-100"
                        onClick={(e) => e.stopPropagation()}
                      >
                        <MoreHorizontal className="h-3 w-3" />
                      </Button>
                    </DropdownMenuTrigger>
                    <DropdownMenuContent align="end">
                      <DropdownMenuItem
                        onClick={(e) => {
                          e.stopPropagation()
                          handleDeleteConversation(conv.id)
                        }}
                        className="text-destructive"
                      >
                        <Trash2 className="h-4 w-4 mr-2" />
                        Delete
                      </DropdownMenuItem>
                    </DropdownMenuContent>
                  </DropdownMenu>
                </div>
              </Card>
            ))}
          </div>
        )}
      </div>
    </div>
  )
}