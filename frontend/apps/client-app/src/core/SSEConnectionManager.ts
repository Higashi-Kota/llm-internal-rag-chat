/**
 * Connection status for SSE streaming
 */
export type ConnectionStatus = "disconnected" | "connecting" | "connected" | "reconnecting"

interface SSEConnectionState {
  readonly status: ConnectionStatus
  readonly lastEventId: string | null
  readonly retryCount: number
}

/**
 * Immutable manager for SSE connection state
 */
export class SSEConnectionManager {
  private constructor(private readonly _state: SSEConnectionState) {}

  static initial(): SSEConnectionManager {
    return new SSEConnectionManager({
      status: "disconnected",
      lastEventId: null,
      retryCount: 0,
    })
  }

  // === Getters ===

  get status(): ConnectionStatus {
    return this._state.status
  }

  get lastEventId(): string | null {
    return this._state.lastEventId
  }

  get retryCount(): number {
    return this._state.retryCount
  }

  get isConnected(): boolean {
    return this._state.status === "connected"
  }

  get isConnecting(): boolean {
    return this._state.status === "connecting" || this._state.status === "reconnecting"
  }

  // === State Transitions (returns new instance) ===

  connecting(): SSEConnectionManager {
    if (this._state.status === "connecting") return this
    return new SSEConnectionManager({
      ...this._state,
      status: "connecting",
    })
  }

  connected(): SSEConnectionManager {
    if (this._state.status === "connected") return this
    return new SSEConnectionManager({
      ...this._state,
      status: "connected",
      retryCount: 0,
    })
  }

  reconnecting(): SSEConnectionManager {
    if (this._state.status === "reconnecting") return this
    return new SSEConnectionManager({
      ...this._state,
      status: "reconnecting",
      retryCount: this._state.retryCount + 1,
    })
  }

  disconnected(): SSEConnectionManager {
    if (this._state.status === "disconnected") return this
    return new SSEConnectionManager({
      ...this._state,
      status: "disconnected",
    })
  }

  setLastEventId(id: string): SSEConnectionManager {
    if (this._state.lastEventId === id) return this
    return new SSEConnectionManager({
      ...this._state,
      lastEventId: id,
    })
  }

  resetRetryCount(): SSEConnectionManager {
    if (this._state.retryCount === 0) return this
    return new SSEConnectionManager({
      ...this._state,
      retryCount: 0,
    })
  }

  reset(): SSEConnectionManager {
    return SSEConnectionManager.initial()
  }
}
