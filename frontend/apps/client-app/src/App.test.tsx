import { render, screen, waitFor } from "@testing-library/react"
import { afterEach, beforeEach, describe, expect, it, vi } from "vitest"
import { App } from "./App"

describe("App", () => {
  const mockFetch = vi.fn()
  const originalFetch = globalThis.fetch

  beforeEach(() => {
    globalThis.fetch = mockFetch
    // Mock successful session list response
    mockFetch.mockResolvedValue({
      ok: true,
      json: () => Promise.resolve({ sessions: [] }),
    })
  })

  afterEach(() => {
    globalThis.fetch = originalFetch
    mockFetch.mockReset()
  })

  describe("rendering", () => {
    it("renders header with title", async () => {
      render(<App />)

      expect(screen.getByRole("heading", { name: "RAG Chat" })).toBeInTheDocument()
      await waitFor(() => {
        expect(mockFetch).toHaveBeenCalled()
      })
    })

    it("renders description text", async () => {
      render(<App />)

      expect(screen.getByText("文書に基づいて質問に回答します")).toBeInTheDocument()
      await waitFor(() => {
        expect(mockFetch).toHaveBeenCalled()
      })
    })

    it("renders chat input", async () => {
      render(<App />)

      expect(screen.getByRole("textbox")).toBeInTheDocument()
      await waitFor(() => {
        expect(mockFetch).toHaveBeenCalled()
      })
    })

    it("renders session sidebar", async () => {
      render(<App />)

      expect(screen.getByRole("heading", { name: "チャット履歴" })).toBeInTheDocument()
      expect(screen.getByRole("button", { name: "新しいチャット" })).toBeInTheDocument()
      expect(screen.getByRole("navigation", { name: "セッション一覧" })).toBeInTheDocument()
      await waitFor(() => {
        expect(mockFetch).toHaveBeenCalled()
      })
    })
  })

  describe("initial state", () => {
    it("does not show model info initially", async () => {
      render(<App />)

      expect(screen.queryByText(/Model:/)).not.toBeInTheDocument()
      await waitFor(() => {
        expect(mockFetch).toHaveBeenCalled()
      })
    })

    it("does not show error when fetch succeeds", async () => {
      render(<App />)

      await waitFor(() => {
        expect(mockFetch).toHaveBeenCalled()
      })

      expect(screen.queryByText(/エラー:/)).not.toBeInTheDocument()
    })
  })

  describe("layout", () => {
    it("renders sidebar and main content", async () => {
      render(<App />)

      // Sidebar should have "チャット履歴" heading
      expect(screen.getByText("チャット履歴")).toBeInTheDocument()

      // Main content should have "RAG Chat" heading
      expect(screen.getByRole("heading", { name: "RAG Chat", level: 1 })).toBeInTheDocument()

      await waitFor(() => {
        expect(mockFetch).toHaveBeenCalled()
      })
    })
  })
})
