"use client"

import { useState, useRef, KeyboardEvent } from "react"
import { Button } from "@/components/ui/button"
import { Textarea } from "@/components/ui/textarea"
import { Send, Paperclip } from "lucide-react"

interface MessageInputProps {
  onSendMessage: (message: string) => void
  disabled?: boolean
  placeholder?: string
}

export function MessageInput({ onSendMessage, disabled, placeholder }: MessageInputProps) {
  const [message, setMessage] = useState("")
  const textareaRef = useRef<HTMLTextAreaElement>(null)

  const handleSend = () => {
    const trimmedMessage = message.trim()
    if (trimmedMessage && !disabled) {
      onSendMessage(trimmedMessage)
      setMessage("")
      // Reset textarea height
      if (textareaRef.current) {
        textareaRef.current.style.height = 'auto'
      }
    }
  }

  const handleKeyDown = (e: KeyboardEvent<HTMLTextAreaElement>) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault()
      handleSend()
    }
  }

  const handleTextareaChange = (e: React.ChangeEvent<HTMLTextAreaElement>) => {
    setMessage(e.target.value)
    
    // Auto-resize textarea
    const textarea = e.target
    textarea.style.height = 'auto'
    textarea.style.height = Math.min(textarea.scrollHeight, 120) + 'px'
  }

  return (
    <div className="flex items-end gap-2 w-full">
      <div className="flex-1 relative">
        <Textarea
          ref={textareaRef}
          value={message}
          onChange={handleTextareaChange}
          onKeyDown={handleKeyDown}
          placeholder={placeholder || "Type your message..."}
          disabled={disabled}
          className="min-h-[44px] max-h-[120px] resize-none pr-12"
          rows={1}
        />
        
        {/* Attachment button (for future use) */}
        <Button
          variant="ghost"
          size="sm"
          className="absolute right-2 top-2 h-8 w-8 p-0"
          disabled={disabled}
        >
          <Paperclip className="h-4 w-4" />
        </Button>
      </div>
      
      <Button
        onClick={handleSend}
        disabled={disabled || !message.trim()}
        size="sm"
        className="h-11 px-4"
      >
        <Send className="h-4 w-4" />
        <span className="sr-only">Send message</span>
      </Button>
    </div>
  )
}
