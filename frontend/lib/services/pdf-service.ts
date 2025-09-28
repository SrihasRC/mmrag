import { api, PDFDocument, PDFUploadResponse } from '../api'

export class PDFService {
  // Upload a PDF file
  static async uploadPDF(file: File): Promise<PDFUploadResponse> {
    return await api.uploadPDF(file)
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
  static async getPDFUrl(_documentId: string): Promise<string> {
    // Backend doesn't provide direct PDF URLs, return a placeholder
    return 'https://mozilla.github.io/pdf.js/web/compressed.tracemonkey-pldi-09.pdf'
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
  static async reprocessDocument(_documentId: string): Promise<void> {
    throw new Error('Reprocessing not supported by backend')
  }
}

// Mock service for development (when backend is not available)
export class MockPDFService {
  private static documents: PDFDocument[] = [
    {
      id: '1',
      filename: 'research-paper.pdf',
      originalName: 'Advanced Machine Learning Research.pdf',
      size: 2048576,
      uploadedAt: '2025-09-28T01:00:00Z',
      status: 'completed',
      pageCount: 15,
      url: 'https://mozilla.github.io/pdf.js/web/compressed.tracemonkey-pldi-09.pdf'
    },
    {
      id: '2',
      filename: 'technical-spec.pdf',
      originalName: 'Technical Specification Document.pdf',
      size: 1024768,
      uploadedAt: '2025-09-28T02:00:00Z',
      status: 'completed',
      pageCount: 8,
      url: 'https://mozilla.github.io/pdf.js/web/compressed.tracemonkey-pldi-09.pdf'
    },
    {
      id: '3',
      filename: 'processing-doc.pdf',
      originalName: 'Document Being Processed.pdf',
      size: 512384,
      uploadedAt: '2025-09-28T02:30:00Z',
      status: 'processing',
      pageCount: undefined
    }
  ]

  static async uploadPDF(file: File): Promise<PDFUploadResponse> {
    // Simulate upload delay
    await new Promise(resolve => setTimeout(resolve, 1000))
    
    const newDoc: PDFDocument = {
      id: Date.now().toString(),
      filename: file.name.toLowerCase().replace(/\s+/g, '-'),
      originalName: file.name,
      size: file.size,
      uploadedAt: new Date().toISOString(),
      status: 'processing',
    }
    
    MockPDFService.documents.unshift(newDoc)
    
    // Simulate processing completion after 3 seconds
    setTimeout(() => {
      const doc = MockPDFService.documents.find(d => d.id === newDoc.id)
      if (doc) {
        doc.status = 'completed'
        doc.pageCount = Math.floor(Math.random() * 20) + 5
        doc.url = 'https://mozilla.github.io/pdf.js/web/compressed.tracemonkey-pldi-09.pdf'
      }
    }, 3000)
    
    return { document: newDoc }
  }

  static async getDocuments(): Promise<PDFDocument[]> {
    // Simulate API delay
    await new Promise(resolve => setTimeout(resolve, 300))
    return [...MockPDFService.documents]
  }

  static async getDocument(documentId: string): Promise<PDFDocument> {
    await new Promise(resolve => setTimeout(resolve, 200))
    const doc = MockPDFService.documents.find(d => d.id === documentId)
    if (!doc) {
      throw new Error('Document not found')
    }
    return doc
  }

  static async deleteDocument(documentId: string): Promise<void> {
    await new Promise(resolve => setTimeout(resolve, 300))
    const index = MockPDFService.documents.findIndex(d => d.id === documentId)
    if (index !== -1) {
      MockPDFService.documents.splice(index, 1)
    }
  }

  static async getPDFUrl(documentId: string): Promise<string> {
    const doc = await this.getDocument(documentId)
    return doc.url || 'https://mozilla.github.io/pdf.js/web/compressed.tracemonkey-pldi-09.pdf'
  }

  static async searchDocuments(query: string): Promise<PDFDocument[]> {
    await new Promise(resolve => setTimeout(resolve, 400))
    return MockPDFService.documents.filter(doc => 
      doc.originalName.toLowerCase().includes(query.toLowerCase()) ||
      doc.filename.toLowerCase().includes(query.toLowerCase())
    )
  }

  static async getProcessingStatus(documentId: string): Promise<{ status: string; progress?: number; error?: string }> {
    const doc = await this.getDocument(documentId)
    return { status: doc.status }
  }

  static async reprocessDocument(documentId: string): Promise<void> {
    await new Promise(resolve => setTimeout(resolve, 500))
    const doc = this.documents.find(d => d.id === documentId)
    if (doc) {
      doc.status = 'processing'
      // Simulate reprocessing
      setTimeout(() => {
        if (doc) {
          doc.status = 'completed'
        }
      }, 2000)
    }
  }
}

// Export the service to use (switch between real and mock)
// Now using correct backend endpoints from README
export const pdfService = PDFService
