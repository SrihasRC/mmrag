import { api, PDFDocument } from '../api'

export class PDFService {
  // Upload a PDF file
  static async uploadPDF(file: File): Promise<{ document: PDFDocument }> {
    const response = await api.uploadPDF(file)
    // Transform backend response to frontend document structure
    const document: PDFDocument = {
      id: response.pdf_id,
      filename: file.name.toLowerCase().replace(/\s+/g, '-'),
      originalName: file.name,
      uploadDate: new Date().toISOString(),
      fileSize: file.size,
      status: response.status === 'completed' ? 'completed' : 'processing',
    }
    return { document }
  }

  // Get all user's PDF documents
  static async getDocuments(): Promise<PDFDocument[]> {
    const result = await api.getPDFs()
    // Transform backend response to match frontend expectations
    const documents = await Promise.all(
      result.processed_pdfs.map(async (pdfId: unknown) => {
        try {
          // Try to get content to extract more info
          const content = await api.getPDFContent(String(pdfId))
          return {
            id: String(pdfId),
            filename: content.original_filename || `Document ${String(pdfId).slice(0, 8)}`,
            originalName: content.original_filename || `Document ${String(pdfId).slice(0, 8)}.pdf`,
            uploadDate: content.upload_date || new Date().toISOString(),
            fileSize: content.file_size || 0,
            status: 'completed' as const,
          }
        } catch {
          // Fallback if content fetch fails
          return {
            id: String(pdfId),
            filename: `Document ${String(pdfId).slice(0, 8)}`,
            originalName: `Document ${String(pdfId).slice(0, 8)}.pdf`,
            uploadDate: new Date().toISOString(),
            fileSize: 0,
            status: 'completed' as const,
          }
        }
      })
    )
    return documents
  }

  // Get a specific PDF document by ID
  static async getDocument(documentId: string): Promise<PDFDocument> {
    await api.getPDFContent(documentId)
    return {
      id: documentId,
      filename: documentId,
      originalName: documentId,
      uploadDate: new Date().toISOString(),
      fileSize: 0,
      status: 'completed' as const,
    }
  }

  // Delete a PDF document
  static async deleteDocument(documentId: string): Promise<void> {
    await api.deletePDF(documentId)
  }

  // Get PDF file URL for viewing
  static async getPDFUrl(documentId: string): Promise<string> {
    // Use the new PDF file serving endpoint
    return `${process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000'}/api/v1/rag/pdf/${documentId}/file`
  }

  // Search documents by filename or content
  static async searchDocuments(query: string): Promise<PDFDocument[]> {
    // Use the vector store search endpoint
    const response = await fetch(`${process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000'}/api/v1/rag/vector-store/search?query=${encodeURIComponent(query)}&k=10`, {
      method: 'POST'
    })
    
    if (!response.ok) {
      throw new Error(`Search failed: ${response.status}`)
    }
    
    const result = await response.json()
    // Transform search results to PDFDocument format
    const uniquePdfIds = [...new Set(result.results?.map((r: { metadata?: { pdf_id?: string } }) => r.metadata?.pdf_id).filter(Boolean))]
    
    return uniquePdfIds.map((pdfId: unknown) => ({
      id: String(pdfId),
      filename: String(pdfId),
      originalName: String(pdfId),
      uploadDate: new Date().toISOString(),
      fileSize: 0,
      status: 'completed' as const,
    }))
  }

  // Get document processing status
  static async getProcessingStatus(documentId: string): Promise<{ status: string; progress?: number; error?: string }> {
    const status = await api.getStatus(documentId)
    return {
      status: status.status || 'completed',
      progress: 100,
    }
  }

  // Reprocess a failed document (not supported by backend)
  static async reprocessDocument(documentId: string): Promise<void> {
    throw new Error(`Reprocessing not supported by backend for document ${documentId}`)
  }
}

// Mock service removed - using real backend service only

// Export the real backend service
export const pdfService = PDFService
