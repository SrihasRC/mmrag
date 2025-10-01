"use client"

import { Button } from "@/components/ui/button"
import { Badge } from "@/components/ui/badge"
import { Card } from "@/components/ui/card"
import { Input } from "@/components/ui/input"
import { Copy, X, Maximize2, Search, ChevronUp, ChevronDown } from "lucide-react"
import { useState, useEffect, useRef, useCallback } from "react"

interface SourceTextModalProps {
  isOpen: boolean
  onClose: () => void
  source: {
    content: string
    pdf_id: string
    page: number
    filename?: string
  }
}

export function SourceTextModal({ isOpen, onClose, source }: SourceTextModalProps) {
  const [copied, setCopied] = useState(false)
  const [searchQuery, setSearchQuery] = useState("")
  const [searchMatches, setSearchMatches] = useState<number[]>([])
  const [currentMatchIndex, setCurrentMatchIndex] = useState(0)
  const contentRef = useRef<HTMLDivElement>(null)

  const copyToClipboard = async () => {
    await navigator.clipboard.writeText(source.content)
    setCopied(true)
    setTimeout(() => setCopied(false), 2000)
  }

  // Search functionality
  useEffect(() => {
    if (!searchQuery.trim()) {
      setSearchMatches([])
      setCurrentMatchIndex(0)
      return
    }

    const matches: number[] = []
    const query = searchQuery.toLowerCase()
    const content = source.content.toLowerCase()
    let index = 0

    while (index < content.length) {
      const foundIndex = content.indexOf(query, index)
      if (foundIndex === -1) break
      matches.push(foundIndex)
      index = foundIndex + 1
    }

    setSearchMatches(matches)
    setCurrentMatchIndex(0)
  }, [searchQuery, source.content])

  const navigateToMatch = useCallback((direction: 'next' | 'prev') => {
    if (searchMatches.length === 0) return
    
    if (direction === 'next') {
      setCurrentMatchIndex((prev) => (prev + 1) % searchMatches.length)
    } else {
      setCurrentMatchIndex((prev) => (prev - 1 + searchMatches.length) % searchMatches.length)
    }
  }, [searchMatches.length])

  // Navigate to current match
  useEffect(() => {
    if (searchMatches.length > 0 && contentRef.current) {
      const matchElements = contentRef.current.querySelectorAll('.search-highlight-current')
      if (matchElements.length > 0) {
        matchElements[0].scrollIntoView({ behavior: 'smooth', block: 'center' })
      }
    }
  }, [currentMatchIndex, searchMatches])

  // Keyboard shortcuts
  useEffect(() => {
    const handleKeyDown = (e: KeyboardEvent) => {
      if (!isOpen) return
      
      if (e.key === 'Escape') {
        onClose()
      } else if (e.key === 'Enter' && searchMatches.length > 0) {
        e.preventDefault()
        navigateToMatch(e.shiftKey ? 'prev' : 'next')
      } else if ((e.ctrlKey || e.metaKey) && e.key === 'f') {
        e.preventDefault()
        // Focus search input
        const searchInput = document.querySelector('input[placeholder="Search in text..."]') as HTMLInputElement
        searchInput?.focus()
      }
    }

    document.addEventListener('keydown', handleKeyDown)
    return () => document.removeEventListener('keydown', handleKeyDown)
  }, [isOpen, onClose, searchMatches.length, navigateToMatch])

  const highlightText = (text: string) => {
    if (!searchQuery.trim()) return text

    const query = searchQuery
    const regex = new RegExp(`(${query.replace(/[.*+?^${}()|[\]\\]/g, '\\$&')})`, 'gi')
    const parts = text.split(regex)

    let matchCount = 0
    return parts.map((part, index) => {
      if (regex.test(part)) {
        const isCurrentMatch = matchCount === currentMatchIndex
        matchCount++
        return (
          <span
            key={index}
            className={`${
              isCurrentMatch 
                ? 'bg-yellow-400 text-black search-highlight-current' 
                : 'bg-yellow-200 text-black'
            } px-1 rounded`}
          >
            {part}
          </span>
        )
      }
      return part
    })
  }

  if (!isOpen) return null

  return (
    <div className="fixed inset-0 z-50 bg-black/80 flex items-center justify-center p-4">
      <Card className="w-full max-w-4xl h-[80vh] flex flex-col bg-background shadow-2xl py-0 gap-0">
        {/* Header */}
        <div className="flex items-center justify-between p-4 border-b">
          <div className="flex items-center gap-2">
            <Maximize2 className="h-4 w-4 text-muted-foreground" />
            <h2 className="font-semibold">Source Text</h2>
            <Badge variant="secondary" className="text-xs">
              Page {source.page}
            </Badge>
          </div>
          <Button
            variant="ghost"
            size="sm"
            onClick={onClose}
            className="h-8 w-8 p-0"
          >
            <X className="h-4 w-4" />
          </Button>
        </div>
        
        {/* Document info and Search */}
        <div className="px-4 py-2 bg-muted/30 border-b space-y-2">
          <p className="text-sm text-muted-foreground">
            {source.filename || `Document ${source.pdf_id.slice(0, 8)}`}
          </p>
          
          {/* Search Bar */}
          <div className="flex items-center gap-2">
            <div className="relative flex-1">
              <Search className="absolute left-2 top-1/2 transform -translate-y-1/2 h-3 w-3 text-muted-foreground" />
              <Input
                type="text"
                placeholder="Search in text..."
                value={searchQuery}
                onChange={(e) => setSearchQuery(e.target.value)}
                className="pl-8 h-8 text-sm"
              />
            </div>
            
            {searchMatches.length > 0 && (
              <div className="flex items-center gap-1">
                <span className="text-xs text-muted-foreground whitespace-nowrap">
                  {currentMatchIndex + 1} of {searchMatches.length}
                </span>
                <Button
                  variant="outline"
                  size="sm"
                  onClick={() => navigateToMatch('prev')}
                  className="h-8 w-8 p-0"
                  disabled={searchMatches.length === 0}
                >
                  <ChevronUp className="h-3 w-3" />
                </Button>
                <Button
                  variant="outline"
                  size="sm"
                  onClick={() => navigateToMatch('next')}
                  className="h-8 w-8 p-0"
                  disabled={searchMatches.length === 0}
                >
                  <ChevronDown className="h-3 w-3" />
                </Button>
              </div>
            )}
            
            {searchQuery && searchMatches.length === 0 && (
              <span className="text-xs text-muted-foreground">No matches</span>
            )}
          </div>
        </div>
        
        {/* Content */}
        <div className="flex-1 overflow-hidden p-4">
          <div className="h-full border rounded-md p-4 bg-muted/10 overflow-y-auto" ref={contentRef}>
            <div className="text-sm leading-relaxed whitespace-pre-wrap font-mono">
              {highlightText(source.content)}
            </div>
          </div>
        </div>
        
        {/* Footer */}
        <div className="flex justify-between items-center p-4 border-t bg-muted/20">
          <div className="text-xs text-muted-foreground">
            {source.content.length.toLocaleString()} characters
          </div>
          <div className="flex gap-2">
            <Button
              variant="outline"
              size="sm"
              onClick={copyToClipboard}
              className="flex items-center gap-1"
            >
              <Copy className="h-3 w-3" />
              {copied ? 'Copied!' : 'Copy Text'}
            </Button>
            <Button variant="default" size="sm" onClick={onClose}>
              Close
            </Button>
          </div>
        </div>
      </Card>
    </div>
  )
}