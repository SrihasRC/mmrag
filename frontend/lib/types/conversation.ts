// Conversation management types for multi-document chat system

export interface Conversation {
  id: string
  pdf_id: string
  pdf_name: string
  messages: Message[]
  created_at: string
  updated_at: string
  last_message_preview?: string
}

export interface Message {
  id: string
  content: string
  role: 'user' | 'assistant'
  timestamp: Date
  sources?: DocumentReference[]
}

export interface DocumentReference {
  pdf_id: string
  filename?: string
  page: number
  content: string
  similarity_score: number
}

export interface ConversationSummary {
  id: string
  pdf_id: string
  pdf_name: string
  title: string
  last_message: string
  updated_at: string
  message_count: number
}

export interface ConversationManager {
  // Core conversation management
  createConversation(pdf_id: string, pdf_name: string): Conversation
  getConversation(conversation_id: string): Conversation | null
  updateConversation(conversation: Conversation): void
  deleteConversation(conversation_id: string): void
  
  // Message management
  addMessage(conversation_id: string, message: Message): void
  getMessages(conversation_id: string): Message[]
  
  // Conversation discovery
  getConversationsForPdf(pdf_id: string): Conversation[]
  getAllConversations(): ConversationSummary[]
  getRecentConversations(limit?: number): ConversationSummary[]
  
  // Utilities
  generateConversationTitle(messages: Message[]): string
  cleanupOldConversations(maxAge?: number): void
}

export interface ConversationState {
  currentConversation: Conversation | null
  conversations: ConversationSummary[]
  isLoading: boolean
}

// Storage keys
export const STORAGE_KEYS = {
  CONVERSATIONS_LIST: 'mmrag_conversations_list',
  CONVERSATION_PREFIX: 'mmrag_conversation_',
  SETTINGS: 'mmrag_conversation_settings'
} as const

export interface ConversationSettings {
  maxConversationsPerPdf: number
  maxMessagesPerConversation: number
  autoCleanupDays: number
}