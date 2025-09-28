"use client"

import { Card } from "@/components/ui/card"
import { Button } from "@/components/ui/button"
import { Badge } from "@/components/ui/badge"
import { Copy, ExternalLink } from "lucide-react"
import { useState } from "react"
import ReactMarkdown from 'react-markdown'
import remarkGfm from 'remark-gfm'
import rehypeHighlight from 'rehype-highlight'
import type { Message } from "./chat-interface"

interface CodeComponentProps {
  inline?: boolean
  className?: string
  children?: React.ReactNode
}

interface MessageBubbleProps {
  message: Message
  onShowPdf: (pdfId: string) => void
}

export function MessageBubble({ message, onShowPdf }: MessageBubbleProps) {
  const [copied, setCopied] = useState(false)

  const copyToClipboard = async () => {
    await navigator.clipboard.writeText(message.content)
    setCopied(true)
    setTimeout(() => setCopied(false), 2000)
  }

  const formatTime = (date: Date) => {
    return date.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })
  }

  return (
    <div className={`flex gap-3 ${message.role === 'user' ? 'justify-end' : 'justify-start'}`}>
      <div className={`max-w-[85%] space-y-2 ${message.role === 'user' ? 'items-end' : 'items-start'}`}>
        <Card className={`p-3 ${
          message.role === 'user' 
            ? 'bg-muted text-primary-foreground ml-auto' 
            : 'bg-card text-card-foreground'
        }`}>
          <div className="space-y-2">
            {message.role === 'assistant' ? (
              <div className="text-sm prose prose-sm max-w-none dark:prose-invert">
                <ReactMarkdown
                  remarkPlugins={[remarkGfm]}
                  rehypePlugins={[rehypeHighlight]}
                  components={{
                    code: ({ inline, className, children, ...props }: CodeComponentProps) => {
                      const match = /language-(\w+)/.exec(className || '')
                      return !inline && match ? (
                        <pre className="bg-muted p-3 rounded-md overflow-x-auto">
                          <code className={className} {...props}>
                            {children}
                          </code>
                        </pre>
                      ) : (
                        <code className="bg-muted px-1 py-0.5 rounded text-sm" {...props}>
                          {children}
                        </code>
                      )
                    },
                    p: ({ children }) => <p className="mb-2 last:mb-0">{children}</p>,
                    ul: ({ children }) => <ul className="list-disc list-inside mb-2">{children}</ul>,
                    ol: ({ children }) => <ol className="list-decimal list-inside mb-2">{children}</ol>,
                    li: ({ children }) => <li className="mb-1">{children}</li>,
                    h1: ({ children }) => <h1 className="text-lg font-bold mb-2">{children}</h1>,
                    h2: ({ children }) => <h2 className="text-base font-bold mb-2">{children}</h2>,
                    h3: ({ children }) => <h3 className="text-sm font-bold mb-2">{children}</h3>,
                    blockquote: ({ children }) => (
                      <blockquote className="border-l-4 border-muted-foreground pl-4 italic mb-2">
                        {children}
                      </blockquote>
                    ),
                  }}
                >
                  {message.content}
                </ReactMarkdown>
              </div>
            ) : (
              <p className="text-sm whitespace-pre-wrap break-words">
                {message.content}
              </p>
            )}
            
            <div className="flex items-center justify-between gap-2">
              <span className={`text-xs ${
                message.role === 'user' 
                  ? 'text-primary-foreground/70' 
                  : 'text-muted-foreground'
              }`}>
                {formatTime(message.timestamp)}
              </span>
              
              <Button
                variant="ghost"
                size="sm"
                onClick={copyToClipboard}
                className={`h-6 w-6 p-0 ${
                  message.role === 'user'
                    ? 'text-primary-foreground/70 hover:text-primary-foreground'
                    : 'text-muted-foreground hover:text-foreground'
                }`}
              >
                <Copy className="h-3 w-3" />
              </Button>
            </div>
          </div>
        </Card>

        {/* Sources */}
        {message.sources && message.sources.length > 0 && (
          <div className="space-y-2">
            <p className="text-xs text-muted-foreground font-medium">
              Sources ({message.sources.length})
            </p>
            <div className="space-y-2">
              {message.sources.map((source, index) => (
                <Card key={index} className="p-3 bg-muted/50">
                  <div className="space-y-2">
                    <div className="flex items-center justify-between">
                      <div className="flex items-center gap-2">
                        <span className="text-xs font-medium text-foreground">
                          {source.filename}
                        </span>
                        <Badge variant="secondary" className="text-xs">
                          Page {source.page}
                        </Badge>
                        <Badge variant="outline" className="text-xs">
                          {Math.round(source.similarity_score * 100)}% match
                        </Badge>
                      </div>
                      
                      <Button
                        variant="ghost"
                        size="sm"
                        onClick={() => onShowPdf(source.pdf_id)}
                        className="h-6 w-6 p-0"
                      >
                        <ExternalLink className="h-3 w-3" />
                      </Button>
                    </div>
                    
                    <p className="text-xs text-muted-foreground line-clamp-2">
                      {source.content}
                    </p>
                  </div>
                </Card>
              ))}
            </div>
          </div>
        )}

        {copied && (
          <div className="text-xs text-green-600">Copied to clipboard!</div>
        )}
      </div>
    </div>
  )
}
