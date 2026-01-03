import { type ConnectionStatus, SSEConnectionManager } from "../core/SSEConnectionManager"

/**
 * Source information for a retrieved document
 */
export interface SourceInfo {
  readonly filename: string
  readonly page?: number
  readonly slide?: number
  readonly sheet?: string
  readonly score: number
}

/**
 * Session summary for sidebar display
 */
export interface SessionSummary {
  readonly id: string
  readonly title: string | null
  readonly createdAt: string
  readonly updatedAt: string
}

/**
 * Chat message
 */
export interface ChatMessage {
  readonly id: string
  readonly role: "user" | "assistant"
  readonly content: string
  readonly sources?: SourceInfo[]
  readonly timestamp: Date
}

/**
 * RAG store snapshot for useSyncExternalStore
 */
export interface RAGSnapshot {
  readonly connectionStatus: ConnectionStatus
  readonly isStreaming: boolean
  readonly messages: ChatMessage[]
  readonly currentResponse: string
  readonly sources: SourceInfo[]
  readonly error: { code: string; message: string } | null
  readonly model: string
  readonly provider: string
  readonly sessionId: string | null
  readonly sessions: SessionSummary[]
  readonly isLoadingSessions: boolean
}

interface RAGStoreConfig {
  readonly apiUrl: string
}

/**
 * RAGStore - External store for RAG chat with SSE streaming
 *
 * Uses useSyncExternalStore protocol for React integration.
 */
export class RAGStore {
  private _connection: SSEConnectionManager
  private _messages: ChatMessage[] = []
  private _currentResponse = ""
  private _sources: SourceInfo[] = []
  private _isStreaming = false
  private _error: { code: string; message: string } | null = null
  private _model = ""
  private _provider = ""
  private _sessionId: string | null = null
  private _abortController: AbortController | null = null
  private readonly _listeners = new Set<() => void>()
  private _snapshot: RAGSnapshot | null = null
  private readonly _config: RAGStoreConfig
  private _sessions: SessionSummary[] = []
  private _isLoadingSessions = false

  private constructor(config: RAGStoreConfig) {
    this._config = config
    this._connection = SSEConnectionManager.initial()
  }

  /**
   * Factory method
   */
  static create(apiUrl: string): RAGStore {
    return new RAGStore({ apiUrl })
  }

  // ==========================================
  // useSyncExternalStore API
  // ==========================================

  /**
   * Subscribe to store changes
   */
  subscribe = (listener: () => void): (() => void) => {
    this._listeners.add(listener)
    return () => this._listeners.delete(listener)
  }

  /**
   * Get current snapshot (returns same reference if unchanged)
   */
  getSnapshot = (): RAGSnapshot => {
    if (this._snapshot === null) {
      this._snapshot = this.createSnapshot()
    }
    return this._snapshot
  }

  private notify(): void {
    this._snapshot = null
    for (const listener of this._listeners) {
      listener()
    }
  }

  private createSnapshot(): RAGSnapshot {
    return {
      connectionStatus: this._connection.status,
      isStreaming: this._isStreaming,
      messages: [...this._messages],
      currentResponse: this._currentResponse,
      sources: [...this._sources],
      error: this._error,
      model: this._model,
      provider: this._provider,
      sessionId: this._sessionId,
      sessions: [...this._sessions],
      isLoadingSessions: this._isLoadingSessions,
    }
  }

  // ==========================================
  // Actions
  // ==========================================

  /**
   * Create a new session
   */
  private async createSession(): Promise<string | null> {
    try {
      const response = await fetch(`${this._config.apiUrl}/api/rag/sessions`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({}),
      })
      if (!response.ok) return null
      const data = (await response.json()) as { id: string }
      return data.id
    } catch {
      return null
    }
  }

  /**
   * Send a message and get RAG response
   */
  async sendMessage(content: string): Promise<void> {
    // Cancel any existing stream
    this.cancelStream()

    // Add user message
    const userMessage: ChatMessage = {
      id: crypto.randomUUID(),
      role: "user",
      content,
      timestamp: new Date(),
    }
    this._messages = [...this._messages, userMessage]

    // Start streaming
    this._isStreaming = true
    this._currentResponse = ""
    this._sources = []
    this._error = null
    this._connection = this._connection.connecting()
    this.notify()

    this._abortController = new AbortController()

    try {
      // Create session if needed (first message)
      if (!this._sessionId) {
        this._sessionId = await this.createSession()
        this.notify()
      }

      // Build request with all messages
      const messages = this._messages.map((m) => ({
        role: m.role,
        content: m.content,
      }))

      const response = await fetch(`${this._config.apiUrl}/api/rag/chat/stream`, {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
          Accept: "text/event-stream",
        },
        body: JSON.stringify({ messages, session_id: this._sessionId }),
        signal: this._abortController.signal,
      })

      if (!response.ok) {
        throw new Error(`HTTP error: ${response.status}`)
      }

      if (!response.body) {
        throw new Error("No response body")
      }

      this._connection = this._connection.connected()
      this.notify()

      await this.processSSEStream(response.body)
    } catch (error) {
      if (error instanceof Error && error.name === "AbortError") {
        this._connection = this._connection.disconnected()
        this._isStreaming = false
        this.notify()
        return
      }

      this._connection = this._connection.disconnected()
      this._isStreaming = false
      this._error = {
        code: "NETWORK_ERROR",
        message: error instanceof Error ? error.message : "接続エラー",
      }
      this.notify()
    }
  }

  private async processSSEStream(body: ReadableStream<Uint8Array>): Promise<void> {
    const reader = body.getReader()
    const decoder = new TextDecoder()
    let buffer = ""

    try {
      while (true) {
        const { done, value } = await reader.read()
        if (done) break

        buffer += decoder.decode(value, { stream: true })
        const lines = buffer.split("\n")
        buffer = lines.pop() ?? ""

        for (const line of lines) {
          this.processSSELine(line)
        }
      }

      // Process remaining buffer
      if (buffer.trim()) {
        this.processSSELine(buffer)
      }
    } finally {
      reader.releaseLock()
      this._connection = this._connection.disconnected()
      this._isStreaming = false
      this.notify()
    }
  }

  private processSSELine(line: string): void {
    if (line.startsWith("id:")) {
      const id = line.slice(3).trim()
      this._connection = this._connection.setLastEventId(id)
      return
    }

    if (line.startsWith("event:")) {
      return
    }

    if (line.startsWith("data:")) {
      const jsonStr = line.slice(5).trim()
      if (!jsonStr) return

      try {
        const data = JSON.parse(jsonStr)
        this.handleSSEData(data)
      } catch {
        // Ignore malformed JSON
      }
    }
  }

  private handleSSEData(data: unknown): void {
    if (!data || typeof data !== "object") return
    const obj = data as Record<string, unknown>

    // Meta event
    if ("trace_id" in obj && "model" in obj && "provider" in obj && !("response" in obj)) {
      this._model = obj.model as string
      this._provider = obj.provider as string
      this.notify()
      return
    }

    // Sources event
    if ("sources" in obj && !("response" in obj)) {
      this._sources = (obj.sources as SourceInfo[]) ?? []
      this.notify()
      return
    }

    // Chunk event
    if ("text" in obj) {
      this._currentResponse += obj.text as string
      this.notify()
      return
    }

    // Done event
    if ("response" in obj && "sources" in obj) {
      const response = obj.response as string
      const sources = (obj.sources as SourceInfo[]) ?? []
      this._model = (obj.model as string) ?? this._model
      this._provider = (obj.provider as string) ?? this._provider

      // Add assistant message
      const assistantMessage: ChatMessage = {
        id: crypto.randomUUID(),
        role: "assistant",
        content: response,
        sources,
        timestamp: new Date(),
      }
      this._messages = [...this._messages, assistantMessage]
      this._currentResponse = ""
      this._sources = sources
      this._isStreaming = false
      this._connection = this._connection.disconnected()
      this.notify()
      return
    }

    // Error event
    if ("code" in obj && "message" in obj) {
      this._error = {
        code: obj.code as string,
        message: obj.message as string,
      }
      this._isStreaming = false
      this._connection = this._connection.disconnected()
      this.notify()
    }
  }

  /**
   * Cancel the current stream
   */
  cancelStream(): void {
    if (this._abortController) {
      this._abortController.abort()
      this._abortController = null
    }
  }

  /**
   * Clear error state
   */
  clearError(): void {
    this._error = null
    this.notify()
  }

  /**
   * Clear all messages and start a new session
   */
  clearMessages(): void {
    this.cancelStream()
    this._messages = []
    this._currentResponse = ""
    this._sources = []
    this._error = null
    this._sessionId = null
    this.notify()
  }

  /**
   * Reset all state
   */
  reset(): void {
    this.cancelStream()
    this._connection = SSEConnectionManager.initial()
    this._messages = []
    this._currentResponse = ""
    this._sources = []
    this._isStreaming = false
    this._error = null
    this._model = ""
    this._provider = ""
    this._sessionId = null
    this.notify()
  }

  // ==========================================
  // Session Management
  // ==========================================

  /**
   * Load session list from API
   */
  async loadSessions(): Promise<void> {
    this._isLoadingSessions = true
    this.notify()

    try {
      const response = await fetch(`${this._config.apiUrl}/api/rag/sessions`)
      if (!response.ok) {
        throw new Error(`HTTP error: ${response.status}`)
      }
      const data = (await response.json()) as {
        sessions: Array<{
          id: string
          title: string | null
          created_at: string
          updated_at: string
        }>
      }
      this._sessions = data.sessions.map((s) => ({
        id: s.id,
        title: s.title,
        createdAt: s.created_at,
        updatedAt: s.updated_at,
      }))
    } catch (error) {
      this._error = {
        code: "LOAD_SESSIONS_ERROR",
        message: error instanceof Error ? error.message : "セッション一覧の取得に失敗しました",
      }
    } finally {
      this._isLoadingSessions = false
      this.notify()
    }
  }

  /**
   * Select a session and restore its messages
   */
  async selectSession(sessionId: string): Promise<void> {
    // Cancel any existing stream
    this.cancelStream()

    this._isLoadingSessions = true
    this._error = null
    this.notify()

    try {
      const response = await fetch(`${this._config.apiUrl}/api/rag/sessions/${sessionId}`)
      if (!response.ok) {
        throw new Error(`HTTP error: ${response.status}`)
      }
      const data = (await response.json()) as {
        session: {
          id: string
          title: string | null
          created_at: string
          updated_at: string
        }
        messages: Array<{
          id: string
          role: "user" | "assistant"
          content: string
          sources: SourceInfo[] | null
          created_at: string
          model: string | null
          provider: string | null
        }>
      }

      this._sessionId = sessionId
      this._messages = data.messages.map((m) => ({
        id: m.id,
        role: m.role,
        content: m.content,
        sources: m.sources ?? undefined,
        timestamp: new Date(m.created_at),
      }))
      this._currentResponse = ""
      this._sources = []
      this._model = data.messages.at(-1)?.model ?? ""
      this._provider = data.messages.at(-1)?.provider ?? ""
    } catch (error) {
      this._error = {
        code: "SELECT_SESSION_ERROR",
        message: error instanceof Error ? error.message : "セッションの読み込みに失敗しました",
      }
    } finally {
      this._isLoadingSessions = false
      this.notify()
    }
  }

  /**
   * Start a new session (clear current and create fresh)
   */
  startNewSession(): void {
    this.cancelStream()
    this._sessionId = null
    this._messages = []
    this._currentResponse = ""
    this._sources = []
    this._error = null
    this._model = ""
    this._provider = ""
    this.notify()
  }
}
