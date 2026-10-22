// Chat session list item
export interface ChatSession {
  sessionId: string
  createdAt: string
  chatCount: number
  title: string
}

// Chat session list response
export interface ChatSessionsResponse {
  total: number
  list: ChatSession[]
}

// Chat message
export interface ChatMessage {
  createdAt: string
  chatType: 1 | 2 | 3 // 1 = user, 2 = AI, 3 = parameter description
  content: string
  audioId: string | null
  macAddress: string
}

// User message content (requires JSON parsing)
export interface UserMessageContent {
  speaker: string
  content: string
}

// Chat session query parameters
export interface GetSessionsParams {
  page: number
  limit: number
}

// Audio playback
export interface AudioResponse {
  data: string // Audio download ID
}
