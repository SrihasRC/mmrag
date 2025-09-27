"use client"

import { ScrollArea } from "@/components/ui/scroll-area"
import { MessageBubble } from "./message-bubble"
import { Loader2 } from "lucide-react"
import type { Message } from "./chat-interface"

interface MessageListProps {
  messages: Message[]
  isLoading: boolean
  onShowPdf: (pdfId: string) => void
}

export function MessageList({ messages, isLoading, onShowPdf }: MessageListProps) {
  return (
    <ScrollArea className="h-full px-4 py-4">
      <div className="space-y-4">
        {messages.map((message) => (
          <MessageBubble
            key={message.id}
            message={message}
            onShowPdf={onShowPdf}
          />
        ))}
        
        {isLoading && (
          <div className="flex items-center gap-2 text-muted-foreground">
            <Loader2 className="h-4 w-4 animate-spin" />
            <span className="text-sm">Thinking...</span>
          </div>
        )}
      </div>
    </ScrollArea>
  )
}
