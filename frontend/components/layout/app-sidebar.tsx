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
import { 
  FileText, 
  Search, 
  MoreHorizontal,
  Loader2,
  AlertCircle
} from "lucide-react"
import { PDFUpload } from "@/components/pdf/pdf-upload"
import { Input } from "@/components/ui/input"

interface PDF {
  id: string
  filename: string
  status: 'processing' | 'completed' | 'error'
  uploadedAt: string
  size?: number
}

interface AppSidebarProps {
  onPdfSelect: (pdfId: string | null) => void
  selectedPdfId: string | null
}

export function AppSidebar({ onPdfSelect, selectedPdfId }: AppSidebarProps) {
  const { state } = useSidebar()
  const [pdfs, setPdfs] = useState<PDF[]>([])
  const [searchQuery, setSearchQuery] = useState("")
  
  const isCollapsed = state === "collapsed"

  // Mock data for now - will be replaced with API calls
  useEffect(() => {
    // Simulate loading PDFs
    const mockPdfs: PDF[] = [
      {
        id: "1",
        filename: "Research Paper.pdf",
        status: "completed",
        uploadedAt: "2025-09-28T01:00:00Z",
        size: 2048000
      },
      {
        id: "2", 
        filename: "Technical Manual.pdf",
        status: "processing",
        uploadedAt: "2025-09-28T01:15:00Z",
        size: 5120000
      }
    ]
    setPdfs(mockPdfs)
  }, [])

  const filteredPdfs = pdfs.filter(pdf => 
    pdf.filename.toLowerCase().includes(searchQuery.toLowerCase())
  )

  const formatFileSize = (bytes: number) => {
    if (bytes === 0) return '0 Bytes'
    const k = 1024
    const sizes = ['Bytes', 'KB', 'MB', 'GB']
    const i = Math.floor(Math.log(bytes) / Math.log(k))
    return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i]
  }

  const getStatusIcon = (status: PDF['status']) => {
    switch (status) {
      case 'processing':
        return <Loader2 className="h-3 w-3 animate-spin text-yellow-500" />
      case 'completed':
        return <FileText className="h-3 w-3 text-green-500" />
      case 'error':
        return <AlertCircle className="h-3 w-3 text-red-500" />
    }
  }

  return (
    <Sidebar className="" collapsible="icon">
      <SidebarHeader className="p-4">
        <div className={`flex items-center gap-2 mb-4 ${isCollapsed ? 'justify-center' : ''}`}>
          <FileText className="h-5 w-5 text-primary" />
          {!isCollapsed && (
            <span className="font-semibold text-sidebar-foreground">Documents</span>
          )}
        </div>
        
        {/* Upload Area - only show when expanded */}
        {!isCollapsed && (
          <>
            <PDFUpload onUploadComplete={(pdf) => {
              setPdfs(prev => [pdf, ...prev])
            }} />
            
            <Separator className="my-4" />
            
            {/* Search */}
            <div className="relative">
              <Search className="absolute left-2 top-2.5 h-4 w-4 text-muted-foreground" />
              <Input
                placeholder="Search documents..."
                value={searchQuery}
                onChange={(e) => setSearchQuery(e.target.value)}
                className="pl-8"
              />
            </div>
          </>
        )}
      </SidebarHeader>

      <SidebarContent>
        <ScrollArea className="flex-1 px-1">
          <SidebarMenu>
            {filteredPdfs.length === 0 ? (
              !isCollapsed && (
                <div className="flex flex-col items-center justify-center py-8 text-center">
                  <FileText className="h-12 w-12 text-muted-foreground mb-2" />
                  <p className="text-sm text-muted-foreground">
                    {searchQuery ? "No documents found" : "No documents uploaded yet"}
                  </p>
                  <p className="text-xs text-muted-foreground mt-1">
                    {searchQuery ? "Try a different search term" : "Upload a PDF to get started"}
                  </p>
                </div>
              )
            ) : (
              filteredPdfs.map((pdf) => (
                <SidebarMenuItem key={pdf.id}>
                  {isCollapsed ? (
                    <SidebarMenuButton
                      onClick={() => onPdfSelect(pdf.id)}
                      className={`w-full justify-center p-2 h-10 ${
                        selectedPdfId === pdf.id ? 'bg-sidebar-accent text-sidebar-primary' : ''
                      }`}
                      title={pdf.filename}
                    >
                      <div className="flex items-center justify-center">
                        {getStatusIcon(pdf.status)}
                      </div>
                    </SidebarMenuButton>
                  ) : (
                    <div className="flex items-start gap-3 w-full p-3 rounded-md hover:bg-sidebar-accent transition-colors">
                      <div className="flex-shrink-0 mt-0.5">
                        {getStatusIcon(pdf.status)}
                      </div>
                      
                      <SidebarMenuButton
                        onClick={() => onPdfSelect(pdf.id)}
                        className={`flex-1 min-w-0 justify-start p-0 h-auto bg-transparent hover:bg-transparent ${
                          selectedPdfId === pdf.id ? 'text-sidebar-primary' : ''
                        }`}
                      >
                        <div className="flex-1 min-w-0">
                          <p className="text-sm font-medium text-sidebar-foreground truncate">
                            {pdf.filename}
                          </p>
                          <div className="flex items-center gap-2 mt-1">
                            <span className="text-xs text-muted-foreground">
                              {pdf.size && formatFileSize(pdf.size)}
                            </span>
                            <span className="text-xs text-muted-foreground">
                              {new Date(pdf.uploadedAt).toLocaleDateString()}
                            </span>
                          </div>
                          {pdf.status === 'processing' && (
                            <p className="text-xs text-yellow-600 mt-1">Processing...</p>
                          )}
                          {pdf.status === 'error' && (
                            <p className="text-xs text-red-600 mt-1">Processing failed</p>
                          )}
                        </div>
                      </SidebarMenuButton>
                      
                      <button
                        className="flex-shrink-0 h-6 w-6 rounded-md hover:bg-sidebar-accent-foreground/10 flex items-center justify-center"
                        onClick={(e) => {
                          e.stopPropagation()
                          // Handle delete
                        }}
                      >
                        <MoreHorizontal className="h-3 w-3" />
                      </button>
                    </div>
                  )}
                </SidebarMenuItem>
              ))
            )}
          </SidebarMenu>
        </ScrollArea>
      </SidebarContent>

      <SidebarFooter className="p-4">
        {!isCollapsed && (
          <div className="text-xs text-muted-foreground">
            {pdfs.length} document{pdfs.length !== 1 ? 's' : ''} uploaded
          </div>
        )}
      </SidebarFooter>
    </Sidebar>
  )
}
