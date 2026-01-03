import { test as base, type Route } from "@playwright/test"

/**
 * Session mock data for sidebar testing
 */
export interface MockSession {
  id: string
  title: string | null
  created_at: string
  updated_at: string
}

export interface MockSessionMessage {
  id: string
  role: "user" | "assistant"
  content: string
  sources: Array<{
    filename: string
    page?: number
    score: number
  }> | null
  created_at: string
  model: string | null
  provider: string | null
}

/**
 * SSE stream mock data for RAG chat testing
 */
export interface MockRAGStreamConfig {
  traceId?: string
  model?: string
  provider?: string
  response?: string
  sources?: Array<{
    filename: string
    page?: number
    slide?: number
    sheet?: string
    score: number
  }>
  /** Delay between SSE events in ms */
  chunkDelay?: number
  /** If set, simulate an error */
  error?: {
    code: string
    message: string
  }
}

const DEFAULT_MOCK_CONFIG: Required<Omit<MockRAGStreamConfig, "error">> = {
  traceId: "test-trace-123",
  model: "llama3.2",
  provider: "ollama",
  response: "これはテスト回答です。ドキュメントに基づいて回答しています。",
  sources: [
    { filename: "document.pdf", page: 1, score: 0.95 },
    { filename: "report.docx", page: 3, score: 0.87 },
  ],
  chunkDelay: 50,
}

/**
 * Create SSE response body for RAG streaming
 */
function createSSEStream(config: MockRAGStreamConfig): string {
  const cfg = { ...DEFAULT_MOCK_CONFIG, ...config }
  const events: string[] = []

  // Meta event
  events.push(
    `id: ${cfg.traceId}:1\n` +
      `event: meta\n` +
      `data: ${JSON.stringify({
        trace_id: cfg.traceId,
        model: cfg.model,
        provider: cfg.provider,
      })}\n\n`,
  )

  if (config.error) {
    // Error event
    events.push(
      `id: ${cfg.traceId}:2\n` +
        `event: error\n` +
        `data: ${JSON.stringify({
          code: config.error.code,
          message: config.error.message,
        })}\n\n`,
    )
  } else {
    // Sources event
    events.push(
      `id: ${cfg.traceId}:2\n` +
        `event: sources\n` +
        `data: ${JSON.stringify({
          sources: cfg.sources,
        })}\n\n`,
    )

    // Simulate streaming chunks (word by word)
    const words = cfg.response.split("")
    let eventId = 3
    for (let i = 0; i < words.length; i += 5) {
      const chunk = words.slice(i, i + 5).join("")
      events.push(
        `id: ${cfg.traceId}:${eventId++}\n` +
          `event: chunk\n` +
          `data: ${JSON.stringify({ text: chunk })}\n\n`,
      )
    }

    // Done event
    events.push(
      `id: ${cfg.traceId}:${eventId}\n` +
        `event: done\n` +
        `data: ${JSON.stringify({
          response: cfg.response,
          sources: cfg.sources,
          model: cfg.model,
          provider: cfg.provider,
        })}\n\n`,
    )
  }

  return events.join("")
}

/**
 * Extended test utilities for RAG chat
 */
interface TestUtils {
  /**
   * Mock the RAG SSE stream API with custom config
   */
  mockRAGStreamAPI: (config?: MockRAGStreamConfig) => Promise<void>

  /**
   * Mock the session list API
   */
  mockSessionsAPI: (sessions: MockSession[]) => Promise<void>

  /**
   * Mock a specific session detail API
   */
  mockSessionDetailAPI: (
    sessionId: string,
    session: MockSession,
    messages: MockSessionMessage[],
  ) => Promise<void>

  /**
   * Mock session creation API
   */
  mockCreateSessionAPI: (sessionId: string) => Promise<void>

  /**
   * Wait for the app to be ready
   */
  waitForApp: () => Promise<void>

  /**
   * Submit a message in the chat input
   */
  submitMessage: (message: string) => Promise<void>

  /**
   * Wait for the assistant response to complete
   */
  waitForResponse: () => Promise<void>

  /**
   * Wait for streaming to start
   */
  waitForStreaming: () => Promise<void>
}

/**
 * Extended test fixture with utilities for RAG chat
 */
export const test = base.extend<{ utils: TestUtils }>({
  utils: async ({ page }, use) => {
    const utils: TestUtils = {
      async mockRAGStreamAPI(config: MockRAGStreamConfig = {}) {
        await page.route("**/api/rag/chat/stream", async (route: Route) => {
          const sseBody = createSSEStream(config)

          await route.fulfill({
            status: 200,
            contentType: "text/event-stream",
            headers: {
              "Cache-Control": "no-cache",
              Connection: "keep-alive",
            },
            body: sseBody,
          })
        })
      },

      async mockSessionsAPI(sessions: MockSession[]) {
        await page.route("**/api/rag/sessions", async (route: Route) => {
          if (route.request().method() === "GET") {
            await route.fulfill({
              status: 200,
              contentType: "application/json",
              body: JSON.stringify({ sessions, total: sessions.length }),
            })
          } else if (route.request().method() === "POST") {
            // Default session creation mock
            await route.fulfill({
              status: 200,
              contentType: "application/json",
              body: JSON.stringify({
                id: "new-session-id",
                title: null,
                created_at: new Date().toISOString(),
                updated_at: new Date().toISOString(),
              }),
            })
          } else {
            await route.continue()
          }
        })
      },

      async mockSessionDetailAPI(
        sessionId: string,
        session: MockSession,
        messages: MockSessionMessage[],
      ) {
        await page.route(`**/api/rag/sessions/${sessionId}`, async (route: Route) => {
          await route.fulfill({
            status: 200,
            contentType: "application/json",
            body: JSON.stringify({ session, messages }),
          })
        })
      },

      async mockCreateSessionAPI(sessionId: string) {
        await page.route("**/api/rag/sessions", async (route: Route) => {
          if (route.request().method() === "POST") {
            await route.fulfill({
              status: 200,
              contentType: "application/json",
              body: JSON.stringify({
                id: sessionId,
                title: null,
                created_at: new Date().toISOString(),
                updated_at: new Date().toISOString(),
              }),
            })
          } else {
            await route.continue()
          }
        })
      },

      async waitForApp() {
        await page.waitForSelector('h1:has-text("RAG Chat")')
      },

      async submitMessage(message: string) {
        const textarea = page.locator("textarea")
        await textarea.fill(message)
        await textarea.press("Control+Enter")
      },

      async waitForResponse() {
        // Wait for assistant message to appear (not streaming)
        await page.waitForSelector(".bg-gray-100:not(:has(.animate-pulse))")
      },

      async waitForStreaming() {
        // Wait for the streaming indicator (pulsing cursor)
        await page.waitForSelector(".animate-pulse")
      },
    }

    await use(utils)
  },
})

export { expect } from "@playwright/test"
