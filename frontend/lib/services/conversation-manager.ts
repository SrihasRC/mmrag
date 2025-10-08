import type { 
  Conversation, 
  ConversationSummary, 
  ConversationManager, 
  ConversationSettings,
  Message 
} from '../types/conversation'
import { STORAGE_KEYS } from '../types/conversation'

class LocalStorageConversationManager implements ConversationManager {
  private settings: ConversationSettings = {
    maxConversationsPerPdf: 10,
    maxMessagesPerConversation: 100,
    autoCleanupDays: 30
  }

  constructor() {
    this.loadSettings()
    this.performAutoCleanup()
  }

  // Core conversation management
  createConversation(pdf_id: string, pdf_name: string): Conversation {
    const conversation: Conversation = {
      id: this.generateId(),
      pdf_id,
      pdf_name,
      messages: [],
      created_at: new Date().toISOString(),
      updated_at: new Date().toISOString()
    }

    this.saveConversation(conversation)
    this.updateConversationsList(conversation)
    return conversation
  }

  // Create a draft conversation that's not saved until first message
  createDraftConversation(pdf_id: string, pdf_name: string): Conversation {
    const conversation: Conversation = {
      id: this.generateId(),
      pdf_id,
      pdf_name,
      messages: [],
      created_at: new Date().toISOString(),
      updated_at: new Date().toISOString()
    }

    // Don't save to storage yet - only save when first message is added
    return conversation
  }

  getConversation(conversation_id: string): Conversation | null {
    try {
      const stored = localStorage.getItem(`${STORAGE_KEYS.CONVERSATION_PREFIX}${conversation_id}`)
      if (!stored) return null
      
      const conversation = JSON.parse(stored) as Conversation
      // Convert timestamp strings back to Date objects
      conversation.messages.forEach(msg => {
        msg.timestamp = new Date(msg.timestamp)
      })
      
      return conversation
    } catch (error) {
      console.error('Error loading conversation:', error)
      return null
    }
  }

  updateConversation(conversation: Conversation): void {
    conversation.updated_at = new Date().toISOString()
    conversation.last_message_preview = this.getLastMessagePreview(conversation.messages)
    
    this.saveConversation(conversation)
    this.updateConversationsList(conversation)
  }

  deleteConversation(conversation_id: string): void {
    // Remove conversation data
    localStorage.removeItem(`${STORAGE_KEYS.CONVERSATION_PREFIX}${conversation_id}`)
    
    // Update conversations list
    const summaries = this.getAllConversations().filter(c => c.id !== conversation_id)
    localStorage.setItem(STORAGE_KEYS.CONVERSATIONS_LIST, JSON.stringify(summaries))
  }

  // Message management
  addMessage(conversation_id: string, message: Message): void {
    const conversation = this.getConversation(conversation_id)
    if (!conversation) {
      throw new Error(`Conversation ${conversation_id} not found`)
    }

    conversation.messages.push(message)
    
    // Limit messages per conversation
    if (conversation.messages.length > this.settings.maxMessagesPerConversation) {
      conversation.messages = conversation.messages.slice(-this.settings.maxMessagesPerConversation)
    }

    this.updateConversation(conversation)
  }

  // Add message to a conversation, saving it if it's the first message
  addMessageToConversation(conversation: Conversation, message: Message): Conversation {
    const isFirstMessage = conversation.messages.length === 0
    
    conversation.messages.push(message)
    conversation.updated_at = new Date().toISOString()
    
    // If this is the first message, save the conversation to storage
    if (isFirstMessage) {
      this.saveConversation(conversation)
      this.updateConversationsList(conversation)
    } else {
      // Update existing conversation
      this.updateConversation(conversation)
    }
    
    return conversation
  }

  getMessages(conversation_id: string): Message[] {
    const conversation = this.getConversation(conversation_id)
    return conversation ? conversation.messages : []
  }

  // Conversation discovery
  getConversationsForPdf(pdf_id: string): Conversation[] {
    const summaries = this.getAllConversations().filter(c => c.pdf_id === pdf_id)
    return summaries.map(s => this.getConversation(s.id)).filter(Boolean) as Conversation[]
  }

  getAllConversations(): ConversationSummary[] {
    try {
      const stored = localStorage.getItem(STORAGE_KEYS.CONVERSATIONS_LIST)
      if (!stored) return []
      
      const summaries = JSON.parse(stored) as ConversationSummary[]
      return summaries.sort((a, b) => new Date(b.updated_at).getTime() - new Date(a.updated_at).getTime())
    } catch (error) {
      console.error('Error loading conversations list:', error)
      return []
    }
  }

  getRecentConversations(limit: number = 5): ConversationSummary[] {
    return this.getAllConversations().slice(0, limit)
  }

  // Utilities
  generateConversationTitle(messages: Message[]): string {
    const userMessages = messages.filter(m => m.role === 'user')
    if (userMessages.length === 0) return 'New Conversation'
    
    const firstMessage = userMessages[0].content
    return firstMessage.length > 50 
      ? firstMessage.substring(0, 50) + '...'
      : firstMessage
  }

  cleanupOldConversations(maxAge: number = this.settings.autoCleanupDays): void {
    const cutoffDate = new Date()
    cutoffDate.setDate(cutoffDate.getDate() - maxAge)
    
    const summaries = this.getAllConversations()
    const toDelete = summaries.filter(c => new Date(c.updated_at) < cutoffDate)
    
    toDelete.forEach(c => this.deleteConversation(c.id))
    
    if (toDelete.length > 0) {
      console.log(`Cleaned up ${toDelete.length} old conversations`)
    }
  }

  // Private helper methods
  private saveConversation(conversation: Conversation): void {
    try {
      localStorage.setItem(
        `${STORAGE_KEYS.CONVERSATION_PREFIX}${conversation.id}`,
        JSON.stringify(conversation)
      )
    } catch (error) {
      console.error('Error saving conversation:', error)
      throw new Error('Failed to save conversation')
    }
  }

  private updateConversationsList(conversation: Conversation): void {
    const summaries = this.getAllConversations()
    const existingIndex = summaries.findIndex(c => c.id === conversation.id)
    
    const summary: ConversationSummary = {
      id: conversation.id,
      pdf_id: conversation.pdf_id,
      pdf_name: conversation.pdf_name,
      title: this.generateConversationTitle(conversation.messages),
      last_message: conversation.last_message_preview || '',
      updated_at: conversation.updated_at,
      message_count: conversation.messages.length
    }

    if (existingIndex >= 0) {
      summaries[existingIndex] = summary
    } else {
      summaries.unshift(summary)
    }

    // Limit conversations per PDF
    const pdfConversations = summaries.filter(c => c.pdf_id === conversation.pdf_id)
    if (pdfConversations.length > this.settings.maxConversationsPerPdf) {
      const excess = pdfConversations.slice(this.settings.maxConversationsPerPdf)
      excess.forEach(c => this.deleteConversation(c.id))
    }

    try {
      localStorage.setItem(STORAGE_KEYS.CONVERSATIONS_LIST, JSON.stringify(summaries))
    } catch (error) {
      console.error('Error updating conversations list:', error)
    }
  }

  private getLastMessagePreview(messages: Message[]): string {
    if (messages.length === 0) return ''
    
    const lastMessage = messages[messages.length - 1]
    return lastMessage.content.length > 100 
      ? lastMessage.content.substring(0, 100) + '...'
      : lastMessage.content
  }

  private generateId(): string {
    return `conv_${Date.now()}_${Math.random().toString(36).substring(2, 9)}`
  }

  private loadSettings(): void {
    try {
      const stored = localStorage.getItem(STORAGE_KEYS.SETTINGS)
      if (stored) {
        this.settings = { ...this.settings, ...JSON.parse(stored) }
      }
    } catch (error) {
      console.error('Error loading settings:', error)
    }
  }

  private performAutoCleanup(): void {
    // Run cleanup on initialization
    setTimeout(() => this.cleanupOldConversations(), 1000)
  }

  // Public settings management
  updateSettings(newSettings: Partial<ConversationSettings>): void {
    this.settings = { ...this.settings, ...newSettings }
    localStorage.setItem(STORAGE_KEYS.SETTINGS, JSON.stringify(this.settings))
  }

  getSettings(): ConversationSettings {
    return { ...this.settings }
  }
}

// Export singleton instance
export const conversationManager = new LocalStorageConversationManager()
export type { ConversationManager }