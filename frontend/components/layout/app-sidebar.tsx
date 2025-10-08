"use client"

import { useState, useEffect } from "react"
import {
  Sidebar,
  SidebarContent,
  SidebarFooter,
  SidebarHeader,
  SidebarMenu,
  SidebarMenuButton,
  SidebarMenuItem,
  useSidebar,
} from "@/components/ui/sidebar"
import { ScrollArea } from "@/components/ui/scroll-area"
import { Separator } from "@/components/ui/separator"
import { Avatar, AvatarFallback, AvatarImage } from "@/components/ui/avatar"
import { 
  MoreHorizontal,
  Settings,
  LogOut,
  User,
  PanelLeftClose,
  PanelLeft,
  Plus,
  MessageCircle,
  Trash2,
} from "lucide-react"
import { Button } from "@/components/ui/button"
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuSeparator,
  DropdownMenuTrigger,
} from "@/components/ui/dropdown-menu"
import { PDFUpload } from "@/components/pdf/pdf-upload"

// Use PDFDocument type from API instead of local interface

import type { Conversation, ConversationSummary } from "@/lib/types/conversation"
import { conversationManager } from "@/lib/services/conversation-manager"

interface AppSidebarProps {
  currentConversation?: Conversation | null
  onConversationSelect?: (conversation: Conversation) => void
  onNewChat?: () => void
}

export function AppSidebar({ 
  currentConversation,
  onConversationSelect,
  onNewChat
}: AppSidebarProps = {}) {
  const { state, toggleSidebar } = useSidebar()
  const [conversations, setConversations] = useState<ConversationSummary[]>([])
  const isCollapsed = state === "collapsed"

  useEffect(() => {
    loadConversations()
  }, [])

  // Refresh conversations when currentConversation changes (new conversation created)
  useEffect(() => {
    if (currentConversation) {
      loadConversations()
    }
  }, [currentConversation])

  const loadConversations = () => {
    const allConversations = conversationManager.getAllConversations()
    setConversations(allConversations.sort((a, b) => 
      new Date(b.updated_at).getTime() - new Date(a.updated_at).getTime()
    ))
  }

  const handleConversationClick = (conversationId: string) => {
    const conversation = conversationManager.getConversation(conversationId)
    if (conversation) {
      onConversationSelect?.(conversation)
    }
  }

  const handleDeleteConversation = (conversationId: string, e: React.MouseEvent) => {
    e.stopPropagation()
    conversationManager.deleteConversation(conversationId)
    loadConversations()
  }

  const formatDate = (dateString: string) => {
    const date = new Date(dateString)
    const now = new Date()
    const diffTime = Math.abs(now.getTime() - date.getTime())
    const diffDays = Math.ceil(diffTime / (1000 * 60 * 60 * 24))
    
    if (diffDays === 1) return 'Today'
    if (diffDays === 2) return 'Yesterday'
    if (diffDays <= 7) return `${diffDays - 1} days ago`
    
    return date.toLocaleDateString('en-US', {
      month: 'short',
      day: 'numeric'
    })
  }

  return (
    <Sidebar variant="inset" className="border-r transition-all duration-50">
      <SidebarHeader className="border-b border-border overflow-hidden">
        <div className="flex items-center">
          <Button
            variant="ghost"
            size="sm"
            onClick={toggleSidebar}
            className="h-8 w-8 p-0 flex-shrink-0"
          >
            {isCollapsed ? (
              <PanelLeft className="h-6 w-6" />
            ) : (
              <PanelLeftClose className="h-6 w-6" />
            )}
          </Button>
          <div className="flex items-center space-x-2 min-w-0">
            {!isCollapsed && (
              <span className="font-semibold truncate text-primary-foreground">MMRag</span>
            )}
          </div>
        </div>
      </SidebarHeader>

      <SidebarContent>
        {!isCollapsed && (
          <div className="p-4 space-y-4">
            <Button
              onClick={onNewChat}
              className="w-full"
              size="sm"
            >
              <Plus className="h-4 w-4 mr-2" />
              New Chat
            </Button>
            
            <PDFUpload onUploadComplete={() => {}} />
          </div>
        )}

        <Separator />

        <ScrollArea className="flex-1">
          <div className="p-1">
            {conversations.length === 0 ? (
              <div className="flex flex-col items-center justify-center py-8 text-center">
                <MessageCircle className="h-12 w-12 text-muted-foreground mb-4" />
                {!isCollapsed && (
                  <div>
                    <p className="text-sm font-medium">No conversations yet</p>
                    <p className="text-xs text-muted-foreground mt-1">
                      Start a new chat to get going
                    </p>
                  </div>
                )}
              </div>
            ) : (
              <SidebarMenu>
                {conversations.map((conv) => (
                  <SidebarMenuItem key={conv.id}>
                    <div className="relative group">
                      <SidebarMenuButton
                        onClick={() => handleConversationClick(conv.id)}
                        isActive={currentConversation?.id === conv.id}
                        className="w-full justify-start p-3 h-auto pr-8"
                      >
                        <div className="flex items-start space-x-3 w-full min-w-0">
                          <div className="flex-shrink-0">
                            <MessageCircle className="h-4 w-4" />
                          </div>
                          
                          {!isCollapsed && (
                            <div className="flex-1 min-w-0 space-y-1">
                              <div className="flex items-center justify-between">
                                <p className="text-sm font-medium truncate">
                                  {conv.title || conv.pdf_name}
                                </p>
                              </div>
                              
                              <div className="flex items-center justify-between text-xs text-muted-foreground">
                                <span>{conv.message_count} messages</span>
                                <span>{formatDate(conv.updated_at)}</span>
                              </div>
                            </div>
                          )}
                        </div>
                      </SidebarMenuButton>
                      
                      {!isCollapsed && (
                        <div className="absolute right-2 top-3 opacity-0 group-hover:opacity-100 transition-opacity">
                          <DropdownMenu>
                            <DropdownMenuTrigger asChild>
                              <button
                                className="h-6 w-6 p-0 rounded hover:bg-accent inline-flex items-center justify-center"
                                onClick={(e) => e.stopPropagation()}
                              >
                                <MoreHorizontal className="h-3 w-3" />
                              </button>
                            </DropdownMenuTrigger>
                            <DropdownMenuContent align="end">
                              <DropdownMenuItem
                                onClick={(e) => handleDeleteConversation(conv.id, e)}
                                className="text-destructive"
                              >
                                <Trash2 className="h-4 w-4 mr-2" />
                                Delete
                              </DropdownMenuItem>
                            </DropdownMenuContent>
                          </DropdownMenu>
                        </div>
                      )}
                    </div>
                  </SidebarMenuItem>
                ))}
              </SidebarMenu>
            )}
          </div>
        {!isCollapsed && (
          <div className="text-xs text-muted-foreground text-center mt-2">
            {conversations.length} conversation{conversations.length !== 1 ? 's' : ''}
          </div>
        )}


        </ScrollArea>
      </SidebarContent>

      <SidebarFooter className="border-t border-border p-1">
        {!isCollapsed && (
          <DropdownMenu>
            <DropdownMenuTrigger asChild>
              <Button variant="ghost" className="w-full justify-start p-2 h-auto">
                <div className="flex items-center space-x-3">
                  <Avatar className="h-8 w-8">
                    <AvatarImage src="/placeholder-avatar.jpg" />
                    <AvatarFallback>U</AvatarFallback>
                  </Avatar>
                  <div className="flex-1 text-left">
                    <p className="text-sm font-medium">Srhs</p>
                    <p className="text-xs text-muted-foreground">srhs@example.com</p>
                  </div>
                  <MoreHorizontal className="h-4 w-4" />
                </div>
              </Button>
            </DropdownMenuTrigger>
            <DropdownMenuContent align="end" className="w-56">
              <DropdownMenuItem>
                <User className="mr-2 h-4 w-4" />
                Profile
              </DropdownMenuItem>
              <DropdownMenuItem>
                <Settings className="mr-2 h-4 w-4" />
                Settings
              </DropdownMenuItem>
              <DropdownMenuSeparator />
              <DropdownMenuItem>
                <LogOut className="mr-2 h-4 w-4" />
                Log out
              </DropdownMenuItem>
            </DropdownMenuContent>
          </DropdownMenu>
        )}
      </SidebarFooter>
    </Sidebar>
  )
}
