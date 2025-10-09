import { api, ChatMessage, ChatRequest, ChatResponse, DocumentReference } from '../api'

export class ChatService {
  // Send a chat message and get AI response
  static async sendMessage(request: ChatRequest): Promise<ChatResponse> {
    const result = await api.queryRAG(
      request.message,
      undefined,  // pdf_id for backward compatibility
      request.documentIds,  // pdf_ids for multi-document support
      5
    )
    
    // Transform backend response to match frontend expectations
    const message: ChatMessage = {
      id: `msg-${Date.now()}`,
      content: result.answer,
      role: 'assistant',
      timestamp: new Date().toISOString(),
    }
    
    const references: DocumentReference[] = result.references?.map((ref: { documentId?: string; pageNumber?: number; snippet?: string; relevanceScore?: number }) => ({
      documentId: ref.documentId || 'unknown',
      pageNumber: ref.pageNumber || 1,
      snippet: ref.snippet || '',
      relevanceScore: ref.relevanceScore || 0.5,
    })) || []
    
    return {
      message,
      references,
    }
  }

  // // Get chat history for a conversation (not implemented in your backend yet)
  // static async getChatHistory(_conversationId: string): Promise<ChatMessage[]> {
  //   // This endpoint doesn't exist in your backend yet, return empty array
  //   return []
  // }

  // // Create a new conversation (not implemented in your backend yet)
  // static async createConversation(): Promise<{ conversationId: string }> {
  //   // Generate a client-side conversation ID since backend doesn't manage conversations yet
  //   return { conversationId: `conv-${Date.now()}` }
  // }

  // // Delete a conversation (not implemented in your backend yet)
  // static async deleteConversation(_conversationId: string): Promise<void> {
  //   // No-op since backend doesn't manage conversations yet
  // }

  // // Get all user conversations (not implemented in your backend yet)
  // static async getConversations(): Promise<Array<{ id: string; title: string; lastMessage: string; updatedAt: string }>> {
  //   // Return empty array since backend doesn't manage conversations yet
  //   return []
  // }
}

export const chatService = ChatService
