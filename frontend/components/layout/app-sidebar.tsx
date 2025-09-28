"use client"

import { useState } from "react"
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
  FileText, 
  Search, 
  MoreHorizontal,
  Loader2,
  Settings,
  LogOut,
  User,
  PanelLeftClose,
  PanelLeft,
} from "lucide-react"
import { Button } from "@/components/ui/button"
import { Input } from "@/components/ui/input"
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuSeparator,
  DropdownMenuTrigger,
} from "@/components/ui/dropdown-menu"
import { PDFUpload } from "@/components/pdf/pdf-upload"
import { pdfService } from "@/lib/services/pdf-service"
import { useApi } from "@/hooks/use-api"

// Use PDFDocument type from API instead of local interface

interface AppSidebarProps {
  onPdfSelect: (pdfId: string | null) => void
  selectedPdfId: string | null
}

export function AppSidebar({ onPdfSelect, selectedPdfId }: AppSidebarProps) {
  const { state, toggleSidebar } = useSidebar()
  const [searchQuery, setSearchQuery] = useState("")
  const isCollapsed = state === "collapsed"

  const {
    data: pdfs = [],
    loading: isLoadingPdfs,
    execute: fetchPdfs
  } = useApi(pdfService.getDocuments, true)

  const handlePdfUpload = () => {
    fetchPdfs()
  }

  const filteredPdfs = (pdfs || []).filter(pdf => 
    pdf.filename.toLowerCase().includes(searchQuery.toLowerCase())
  )

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
            <div className="relative">
              <Search className="absolute left-3 top-1/2 h-4 w-4 -translate-y-1/2 text-muted-foreground" />
              <Input
                placeholder="Search documents..."
                value={searchQuery}
                onChange={(e) => setSearchQuery(e.target.value)}
                className="pl-9"
              />
            </div>

            {/* Upload Area */}
            <PDFUpload onUploadComplete={handlePdfUpload} />
          </div>
        )}

        <Separator />

        <ScrollArea className="flex-1">
          <div className="p-1">
            {isLoadingPdfs ? (
              <div className="flex items-center justify-center py-8">
                <Loader2 className="h-6 w-6 animate-spin" />
              </div>
            ) : filteredPdfs.length === 0 ? (
              <div className="flex flex-col items-center justify-center py-8 text-center">
                <FileText className="h-12 w-12 text-muted-foreground mb-4" />
                {!isCollapsed && (
                  <div>
                    <p className="text-sm font-medium">No documents yet</p>
                    <p className="text-xs text-muted-foreground mt-1">
                      Upload a PDF to get started
                    </p>
                  </div>
                )}
              </div>
            ) : (
              <SidebarMenu>
                {filteredPdfs.map((pdf) => (
                  <SidebarMenuItem key={pdf.id}>
                    <SidebarMenuButton
                      onClick={() => onPdfSelect(pdf.id)}
                      isActive={selectedPdfId === pdf.id}
                      className="w-full justify-start p-3 h-auto"
                    >
                      <div className="flex items-start space-x-3 w-full min-w-0">
                        <div className="flex-shrink-0">
                          <FileText className="h-5 w-5 text-blue-500" />
                        </div>
                        
                        {!isCollapsed && (
                          <div className="flex-1 min-w-0 space-y-1">
                            <div className="flex items-center justify-between">
                              <p className="text-sm font-medium truncate">
                                {pdf.filename}
                              </p>
                            </div>
                            
                            <div className="flex items-center justify-between text-xs text-muted-foreground">
                              <span>{formatFileSize(pdf.fileSize)} • {formatDate(pdf.uploadDate)}</span>
                              <div className="flex items-center space-x-1">
                                {pdf.status === 'processing' && (
                                  <Loader2 className="h-3 w-3 animate-spin" />
                                )}
                                {pdf.status === 'completed' && (
                                  <div className="h-2 w-2 bg-green-500 rounded-full" />
                                )}
                              </div>
                            </div>
                          </div>
                        )}
                      </div>
                    </SidebarMenuButton>
                  </SidebarMenuItem>
                ))}
              </SidebarMenu>
            )}
          </div>
        </ScrollArea>
      </SidebarContent>

      <SidebarFooter className="border-t border-border p-4">
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
                    <p className="text-sm font-medium">User</p>
                    <p className="text-xs text-muted-foreground">user@example.com</p>
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
        
        {!isCollapsed && (
          <div className="text-xs text-muted-foreground text-center mt-2">
            {filteredPdfs.length} document{filteredPdfs.length !== 1 ? 's' : ''}
          </div>
        )}
      </SidebarFooter>
    </Sidebar>
  )
}
