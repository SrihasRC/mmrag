// API Configuration and Base Client
const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000'

// Types for API responses based on backend models
export interface PDFDocument {
  id: string
  filename: string
  originalName: string
  uploadDate: string
  fileSize: number
  status: 'processing' | 'completed' | 'failed'
}

export interface PDFUploadResponse {
  pdf_id: string
  processing_summary: {
    total_chunks: number
    texts_count: number
    tables_count: number
    images_count: number
  }
  summaries: {
    text: string[]
    tables: string[]
    images: string[]
  }
  storage_result?: Record<string, unknown>
  embedding_result: Record<string, unknown>
  status: string
}

export interface ChatMessage {
  id: string
  content: string
  role: 'user' | 'assistant'
  timestamp: string
  sources?: DocumentReference[]
}

export interface ChatRequest {
  message: string
  conversationId?: string
  documentIds?: string[]
}

export interface ChatResponse {
  message: ChatMessage
  references?: DocumentReference[]
}

export interface DocumentReference {
  documentId: string
  pageNumber: number
  snippet: string
  relevanceScore: number
}

// Simple API functions that match backend exactly
export const api = {
  // Upload PDF - matches backend: file: UploadFile = File(...), save_content: bool = Query(True)
  async uploadPDF(file: File): Promise<PDFUploadResponse> {
    const formData = new FormData()
    formData.append('file', file)
    
    const url = `${API_BASE_URL}/api/v1/rag/upload?save_content=true`
    
    console.log('📤 Uploading PDF:', { 
      filename: file.name, 
      size: file.size, 
      type: file.type,
      url 
    })
    
    const response = await fetch(url, {
      method: 'POST',
      body: formData,
      // Don't set Content-Type header - let browser set it with boundary for multipart/form-data
    })
    
    if (!response.ok) {
      const errorText = await response.text()
      console.error('❌ Upload failed:', { 
        status: response.status, 
        statusText: response.statusText,
        error: errorText 
      })
      throw new Error(`Upload failed: ${response.status} ${response.statusText} - ${errorText}`)
    }
    
    const result = await response.json()
    console.log('✅ Upload success:', result)
    return result
  },

  // Get list of processed PDFs
  async getPDFs(): Promise<{ processed_pdfs: string[], count: number }> {
    const response = await fetch(`${API_BASE_URL}/api/v1/rag/pdfs`)
    
    if (!response.ok) {
      throw new Error(`Failed to get PDFs: ${response.status} ${response.statusText}`)
    }
    
    return response.json()
  },

  // Query RAG system - matches backend: QueryRequest model
  async queryRAG(question: string, pdf_id?: string, top_k: number = 5): Promise<{
    question: string
    answer: string
    references: DocumentReference[]
    sources: Record<string, unknown>[]
    pdf_id: string | null
    retrieved_docs_count: number
  }> {
    const payload = {
      question,
      pdf_id: pdf_id || null,
      top_k
    }
    
    console.log('🔍 RAG Query:', payload)
    
    const response = await fetch(`${API_BASE_URL}/api/v1/rag/query`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify(payload),
    })
    
    if (!response.ok) {
      const errorText = await response.text()
      console.error('❌ Query failed:', { 
        status: response.status, 
        statusText: response.statusText,
        error: errorText 
      })
      throw new Error(`Query failed: ${response.status} ${response.statusText}`)
    }
    
    const result = await response.json()
    console.log('✅ Query success:', result)
    return result
  },

  // Get processing status
  async getStatus(pdf_id: string): Promise<{
    pdf_id: string
    content_stored: boolean
    embeddings_created: boolean
    status: string
  }> {
    const response = await fetch(`${API_BASE_URL}/api/v1/rag/status/${pdf_id}`)
    
    if (!response.ok) {
      throw new Error(`Failed to get status: ${response.status} ${response.statusText}`)
    }
    
    return response.json()
  },

  // Delete PDF
  async deletePDF(pdf_id: string): Promise<{
    message: string
    deleted_items: Record<string, unknown>
  }> {
    const response = await fetch(`${API_BASE_URL}/api/v1/rag/pdf/${pdf_id}`, {
      method: 'DELETE',
    })
    
    if (!response.ok) {
      throw new Error(`Failed to delete PDF: ${response.status} ${response.statusText}`)
    }
    
    return response.json()
  },

  // Get PDF content
  async getPDFContent(pdf_id: string): Promise<{
    pdf_id: string
    metadata: Record<string, unknown>
    original_filename: string
    file_size: number
    upload_date: string
    text_files: string[]
    table_files: string[]
    image_files: string[]
    summary_files: string[]
  }> {
    const response = await fetch(`${API_BASE_URL}/api/v1/rag/content/${pdf_id}`)
    
    if (!response.ok) {
      throw new Error(`Failed to get PDF content: ${response.status} ${response.statusText}`)
    }
    
    return response.json()
  },

  // Health check
  async healthCheck(): Promise<{
    status: string
    vector_store: Record<string, unknown>
    services: Record<string, string>
  }> {
    const response = await fetch(`${API_BASE_URL}/api/v1/rag/health`)
    
    if (!response.ok) {
      throw new Error(`Health check failed: ${response.status} ${response.statusText}`)
    }
    
    return response.json()
  }
}

// Legacy exports for compatibility with existing services
export const apiClient = {
  uploadFile: async <T>(endpoint: string, file: File): Promise<{ data: T }> => {
    if (endpoint === '/api/v1/rag/upload') {
      const result = await api.uploadPDF(file)
      return { data: result as T }
    }
    throw new Error('Unsupported endpoint')
  },
  get: async <T>(endpoint: string): Promise<{ data: T }> => {
    if (endpoint === '/api/v1/rag/pdfs') {
      const result = await api.getPDFs()
      return { data: result as T }
    }
    throw new Error('Unsupported endpoint')
  },
  post: async <T>(endpoint: string, data: Record<string, unknown>): Promise<{ data: T }> => {
    if (endpoint === '/api/v1/rag/query') {
      const result = await api.queryRAG(
        data.question as string, 
        data.pdf_id as string | undefined, 
        data.top_k as number | undefined
      )
      return { data: result as T }
    }
    throw new Error('Unsupported endpoint')
  },
  delete: async <T>(endpoint: string): Promise<{ data: T }> => {
    const match = endpoint.match(/\/api\/v1\/rag\/pdf\/(.+)/)
    if (match) {
      const result = await api.deletePDF(match[1])
      return { data: result as T }
    }
    throw new Error('Unsupported endpoint')
  }
}

export class ApiError extends Error {
  public code: string
  public details?: Record<string, unknown>

  constructor({ message, code = 'API_ERROR', details }: { message: string; code?: string; details?: Record<string, unknown> }) {
    super(message)
    this.name = 'ApiError'
    this.code = code
    this.details = details
  }
}

// Additional types for compatibility
export interface ApiResponse<T> {
  data: T
  message?: string
  success: boolean
}
