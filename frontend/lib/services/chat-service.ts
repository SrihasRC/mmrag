import { api, ChatMessage, ChatRequest, ChatResponse, DocumentReference } from '../api'

export class ChatService {
  // Send a chat message and get AI response
  static async sendMessage(request: ChatRequest): Promise<ChatResponse> {
    const result = await api.queryRAG(
      request.message,
      request.documentIds?.[0],
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

  // Get chat history for a conversation (not implemented in your backend yet)
  static async getChatHistory(conversationId: string): Promise<ChatMessage[]> {
    // This endpoint doesn't exist in your backend yet, return empty array
    return []
  }

  // Create a new conversation (not implemented in your backend yet)
  static async createConversation(): Promise<{ conversationId: string }> {
    // Generate a client-side conversation ID since backend doesn't manage conversations yet
    return { conversationId: `conv-${Date.now()}` }
  }

  // Delete a conversation (not implemented in your backend yet)
  static async deleteConversation(conversationId: string): Promise<void> {
    // No-op since backend doesn't manage conversations yet
  }

  // Get all user conversations (not implemented in your backend yet)
  static async getConversations(): Promise<Array<{ id: string; title: string; lastMessage: string; updatedAt: string }>> {
    // Return empty array since backend doesn't manage conversations yet
    return []
  }
}

// Mock service for development
export class MockChatService {
  private static conversations: Map<string, ChatMessage[]> = new Map()
  private static conversationCounter = 1

  static async sendMessage(request: ChatRequest): Promise<ChatResponse> {
    // Simulate API delay
    await new Promise(resolve => setTimeout(resolve, 1500))

    const conversationId = request.conversationId || `conv-${this.conversationCounter++}`
    
    // Get or create conversation history
    if (!this.conversations.has(conversationId)) {
      this.conversations.set(conversationId, [])
    }
    
    const history = this.conversations.get(conversationId)!
    
    // Add user message
    const userMessage: ChatMessage = {
      id: `msg-${Date.now()}-user`,
      content: request.message,
      role: 'user',
      timestamp: new Date().toISOString(),
    }
    
    history.push(userMessage)

    // Generate mock AI response
    const mockResponses = [
      "Based on the documents you've uploaded, I can see that this topic is covered in several sections. Let me provide you with a comprehensive answer.",
      "That's an interesting question! According to the research papers in your collection, there are several key points to consider.",
      "I found relevant information across multiple documents. Here's what the research indicates about your question.",
      "Great question! The documents contain detailed information about this topic. Let me break it down for you.",
      "From analyzing your PDF documents, I can provide insights on this topic with specific references to the source material."
    ]

    const mockReferences: DocumentReference[] = [
      {
        documentId: '1',
        pageNumber: Math.floor(Math.random() * 10) + 1,
        snippet: "This section discusses the methodology used in the research and provides detailed analysis of the results obtained through extensive experimentation.",
        relevanceScore: 0.95,
        boundingBox: {
          x: 100,
          y: 200,
          width: 400,
          height: 60
        }
      },
      {
        documentId: '2',
        pageNumber: Math.floor(Math.random() * 8) + 1,
        snippet: "The technical specifications outlined in this document provide a comprehensive framework for understanding the implementation details.",
        relevanceScore: 0.87,
        boundingBox: {
          x: 120,
          y: 350,
          width: 380,
          height: 45
        }
      }
    ]

    const aiMessage: ChatMessage = {
      id: `msg-${Date.now()}-ai`,
      content: mockResponses[Math.floor(Math.random() * mockResponses.length)] + 
               "\n\nI've found relevant information in your documents that addresses your question. " +
               "The research shows several important findings that are directly applicable to your inquiry.",
      role: 'assistant',
      timestamp: new Date().toISOString(),
      documentReferences: mockReferences,
    }

    history.push(aiMessage)

    return {
      message: aiMessage,
      conversationId,
      references: mockReferences,
    }
  }

  static async getChatHistory(conversationId: string): Promise<ChatMessage[]> {
    await new Promise(resolve => setTimeout(resolve, 300))
    return this.conversations.get(conversationId) || []
  }

  static async createConversation(): Promise<{ conversationId: string }> {
    await new Promise(resolve => setTimeout(resolve, 200))
    const conversationId = `conv-${this.conversationCounter++}`
    this.conversations.set(conversationId, [])
    return { conversationId }
  }

  static async deleteConversation(conversationId: string): Promise<void> {
    await new Promise(resolve => setTimeout(resolve, 300))
    this.conversations.delete(conversationId)
  }

  static async getConversations(): Promise<Array<{ id: string; title: string; lastMessage: string; updatedAt: string }>> {
    await new Promise(resolve => setTimeout(resolve, 400))
    
    const conversations = Array.from(this.conversations.entries()).map(([id, messages]) => {
      const lastMessage = messages[messages.length - 1]
      return {
        id,
        title: messages.length > 0 ? 
          (messages[0].content.substring(0, 50) + (messages[0].content.length > 50 ? '...' : '')) : 
          'New Conversation',
        lastMessage: lastMessage ? lastMessage.content.substring(0, 100) : '',
        updatedAt: lastMessage ? lastMessage.timestamp : new Date().toISOString(),
      }
    })

    return conversations.sort((a, b) => new Date(b.updatedAt).getTime() - new Date(a.updatedAt).getTime())
  }
}

// Export the service to use (switch between real and mock)
// Now using correct backend endpoints from README
export const chatService = ChatService
