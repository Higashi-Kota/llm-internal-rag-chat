import { afterEach, beforeEach, describe, expect, it, vi } from "vitest"
import { RAGStore } from "./RAGStore"

describe("RAGStore", () => {
  describe("useSyncExternalStore protocol", () => {
    it("creates store with initial state", () => {
      const store = RAGStore.create("")
      const snapshot = store.getSnapshot()

      expect(snapshot.connectionStatus).toBe("disconnected")
      expect(snapshot.isStreaming).toBe(false)
      expect(snapshot.messages).toEqual([])
      expect(snapshot.currentResponse).toBe("")
      expect(snapshot.sources).toEqual([])
      expect(snapshot.error).toBeNull()
      expect(snapshot.model).toBe("")
      expect(snapshot.provider).toBe("")
      expect(snapshot.sessions).toEqual([])
      expect(snapshot.isLoadingSessions).toBe(false)
      expect(snapshot.sessionId).toBeNull()
    })

    it("returns same snapshot reference when unchanged", () => {
      const store = RAGStore.create("")
      const snapshot1 = store.getSnapshot()
      const snapshot2 = store.getSnapshot()

      expect(snapshot1).toBe(snapshot2)
    })

    it("notifies subscribers on state change", () => {
      const store = RAGStore.create("")
      const listener = vi.fn()

      store.subscribe(listener)
      store.clearError() // triggers notify

      expect(listener).toHaveBeenCalledTimes(1)
    })

    it("unsubscribes correctly", () => {
      const store = RAGStore.create("")
      const listener = vi.fn()

      const unsubscribe = store.subscribe(listener)
      unsubscribe()
      store.clearError()

      expect(listener).not.toHaveBeenCalled()
    })

    it("supports multiple subscribers", () => {
      const store = RAGStore.create("")
      const listener1 = vi.fn()
      const listener2 = vi.fn()

      store.subscribe(listener1)
      store.subscribe(listener2)
      store.clearError()

      expect(listener1).toHaveBeenCalledTimes(1)
      expect(listener2).toHaveBeenCalledTimes(1)
    })
  })

  describe("actions", () => {
    it("clears messages", () => {
      const store = RAGStore.create("")
      store.clearMessages()
      const snapshot = store.getSnapshot()

      expect(snapshot.messages).toEqual([])
      expect(snapshot.currentResponse).toBe("")
      expect(snapshot.sources).toEqual([])
      expect(snapshot.error).toBeNull()
    })

    it("resets all state", () => {
      const store = RAGStore.create("")
      store.reset()
      const snapshot = store.getSnapshot()

      expect(snapshot.connectionStatus).toBe("disconnected")
      expect(snapshot.isStreaming).toBe(false)
      expect(snapshot.messages).toEqual([])
      expect(snapshot.currentResponse).toBe("")
      expect(snapshot.sources).toEqual([])
      expect(snapshot.error).toBeNull()
      expect(snapshot.model).toBe("")
      expect(snapshot.provider).toBe("")
    })

    it("clears error state", () => {
      const store = RAGStore.create("")
      store.clearError()
      const snapshot = store.getSnapshot()

      expect(snapshot.error).toBeNull()
    })
  })

  describe("snapshot immutability", () => {
    it("creates new snapshot after state change", () => {
      const store = RAGStore.create("")
      const snapshot1 = store.getSnapshot()
      store.clearMessages()
      const snapshot2 = store.getSnapshot()

      expect(snapshot1).not.toBe(snapshot2)
    })
  })

  describe("session management", () => {
    const mockFetch = vi.fn()
    const originalFetch = globalThis.fetch

    beforeEach(() => {
      globalThis.fetch = mockFetch
      mockFetch.mockReset()
    })

    afterEach(() => {
      globalThis.fetch = originalFetch
    })

    describe("loadSessions", () => {
      it("loads sessions from API", async () => {
        const mockSessions = {
          sessions: [
            {
              id: "session-1",
              title: "Test Session",
              created_at: "2024-01-01T00:00:00Z",
              updated_at: "2024-01-01T01:00:00Z",
            },
            {
              id: "session-2",
              title: null,
              created_at: "2024-01-02T00:00:00Z",
              updated_at: "2024-01-02T01:00:00Z",
            },
          ],
        }
        mockFetch.mockResolvedValueOnce({
          ok: true,
          json: () => Promise.resolve(mockSessions),
        })

        const store = RAGStore.create("http://localhost:8000")
        await store.loadSessions()
        const snapshot = store.getSnapshot()

        expect(mockFetch).toHaveBeenCalledWith("http://localhost:8000/api/rag/sessions")
        expect(snapshot.sessions).toHaveLength(2)
        expect(snapshot.sessions[0]).toEqual({
          id: "session-1",
          title: "Test Session",
          createdAt: "2024-01-01T00:00:00Z",
          updatedAt: "2024-01-01T01:00:00Z",
        })
        expect(snapshot.sessions[1].title).toBeNull()
        expect(snapshot.isLoadingSessions).toBe(false)
      })

      it("sets loading state while fetching", async () => {
        let resolvePromise: ((value: unknown) => void) | undefined
        const pendingPromise = new Promise((resolve) => {
          resolvePromise = resolve
        })
        mockFetch.mockReturnValueOnce(pendingPromise)

        const store = RAGStore.create("http://localhost:8000")
        const loadPromise = store.loadSessions()

        expect(store.getSnapshot().isLoadingSessions).toBe(true)

        resolvePromise?.({
          ok: true,
          json: () => Promise.resolve({ sessions: [] }),
        })
        await loadPromise

        expect(store.getSnapshot().isLoadingSessions).toBe(false)
      })

      it("sets error on API failure", async () => {
        mockFetch.mockResolvedValueOnce({
          ok: false,
          status: 500,
        })

        const store = RAGStore.create("http://localhost:8000")
        await store.loadSessions()
        const snapshot = store.getSnapshot()

        expect(snapshot.error).not.toBeNull()
        expect(snapshot.error?.code).toBe("LOAD_SESSIONS_ERROR")
        expect(snapshot.isLoadingSessions).toBe(false)
      })

      it("sets error on network failure", async () => {
        mockFetch.mockRejectedValueOnce(new Error("Network error"))

        const store = RAGStore.create("http://localhost:8000")
        await store.loadSessions()
        const snapshot = store.getSnapshot()

        expect(snapshot.error).not.toBeNull()
        expect(snapshot.error?.code).toBe("LOAD_SESSIONS_ERROR")
        expect(snapshot.error?.message).toBe("Network error")
      })
    })

    describe("selectSession", () => {
      it("loads and restores session messages", async () => {
        const mockSessionData = {
          session: {
            id: "session-1",
            title: "Test Session",
            created_at: "2024-01-01T00:00:00Z",
            updated_at: "2024-01-01T01:00:00Z",
          },
          messages: [
            {
              id: "msg-1",
              role: "user",
              content: "Hello",
              sources: null,
              created_at: "2024-01-01T00:00:00Z",
              model: null,
              provider: null,
            },
            {
              id: "msg-2",
              role: "assistant",
              content: "Hi there!",
              sources: [{ filename: "test.pdf", page: 1, score: 0.9 }],
              created_at: "2024-01-01T00:01:00Z",
              model: "gemma3:4b",
              provider: "ollama",
            },
          ],
        }
        mockFetch.mockResolvedValueOnce({
          ok: true,
          json: () => Promise.resolve(mockSessionData),
        })

        const store = RAGStore.create("http://localhost:8000")
        await store.selectSession("session-1")
        const snapshot = store.getSnapshot()

        expect(mockFetch).toHaveBeenCalledWith("http://localhost:8000/api/rag/sessions/session-1")
        expect(snapshot.sessionId).toBe("session-1")
        expect(snapshot.messages).toHaveLength(2)
        expect(snapshot.messages[0].content).toBe("Hello")
        expect(snapshot.messages[1].content).toBe("Hi there!")
        expect(snapshot.messages[1].sources).toHaveLength(1)
        expect(snapshot.model).toBe("gemma3:4b")
        expect(snapshot.provider).toBe("ollama")
      })

      it("sets error on session not found", async () => {
        mockFetch.mockResolvedValueOnce({
          ok: false,
          status: 404,
        })

        const store = RAGStore.create("http://localhost:8000")
        await store.selectSession("nonexistent")
        const snapshot = store.getSnapshot()

        expect(snapshot.error).not.toBeNull()
        expect(snapshot.error?.code).toBe("SELECT_SESSION_ERROR")
      })
    })

    describe("startNewSession", () => {
      it("clears current session and messages", () => {
        const store = RAGStore.create("http://localhost:8000")

        // Simulate having a session
        store.startNewSession()
        const snapshot = store.getSnapshot()

        expect(snapshot.sessionId).toBeNull()
        expect(snapshot.messages).toEqual([])
        expect(snapshot.currentResponse).toBe("")
        expect(snapshot.sources).toEqual([])
        expect(snapshot.error).toBeNull()
      })

      it("notifies subscribers", () => {
        const store = RAGStore.create("http://localhost:8000")
        const listener = vi.fn()

        store.subscribe(listener)
        store.startNewSession()

        expect(listener).toHaveBeenCalled()
      })
    })
  })
})
