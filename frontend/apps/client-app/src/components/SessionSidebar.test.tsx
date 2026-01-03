import { render, screen } from "@testing-library/react"
import userEvent from "@testing-library/user-event"
import { describe, expect, it, vi } from "vitest"
import type { SessionSummary } from "../store/RAGStore"
import { SessionSidebar } from "./SessionSidebar"

const mockSessions: SessionSummary[] = [
  {
    id: "session-1",
    title: "Test Session",
    createdAt: "2024-01-15T10:00:00Z",
    updatedAt: "2024-01-15T11:00:00Z",
  },
  {
    id: "session-2",
    title: null,
    createdAt: "2024-01-14T10:00:00Z",
    updatedAt: "2024-01-14T11:00:00Z",
  },
]

describe("SessionSidebar", () => {
  const defaultProps = {
    sessions: mockSessions,
    currentSessionId: null,
    isLoading: false,
    onSelectSession: vi.fn(),
    onNewSession: vi.fn(),
  }

  describe("rendering", () => {
    it("renders header", () => {
      render(<SessionSidebar {...defaultProps} />)

      expect(screen.getByRole("heading", { name: "チャット履歴" })).toBeInTheDocument()
    })

    it("renders new chat button", () => {
      render(<SessionSidebar {...defaultProps} />)

      expect(screen.getByRole("button", { name: "新しいチャット" })).toBeInTheDocument()
    })

    it("renders session list", () => {
      render(<SessionSidebar {...defaultProps} />)

      expect(screen.getByRole("navigation", { name: "セッション一覧" })).toBeInTheDocument()
      expect(screen.getByText("Test Session")).toBeInTheDocument()
    })

    it("displays session title or fallback text", () => {
      render(<SessionSidebar {...defaultProps} />)

      expect(screen.getByText("Test Session")).toBeInTheDocument()
      // Session with null title shows fallback
      expect(screen.getAllByText("新しいチャット")).toHaveLength(2) // button + fallback title
    })
  })

  describe("loading state", () => {
    it("shows loading spinner when loading", () => {
      render(<SessionSidebar {...defaultProps} isLoading={true} sessions={[]} />)

      // Check for spinner element (has animate-spin class)
      const spinner = document.querySelector(".animate-spin")
      expect(spinner).toBeInTheDocument()
    })

    it("does not show sessions while loading", () => {
      render(<SessionSidebar {...defaultProps} isLoading={true} />)

      expect(screen.queryByText("Test Session")).not.toBeInTheDocument()
    })
  })

  describe("empty state", () => {
    it("shows empty message when no sessions", () => {
      render(<SessionSidebar {...defaultProps} sessions={[]} />)

      expect(screen.getByText("チャット履歴がありません")).toBeInTheDocument()
    })
  })

  describe("selection", () => {
    it("highlights current session", () => {
      render(<SessionSidebar {...defaultProps} currentSessionId='session-1' />)

      const selectedButton = screen.getByRole("button", { name: /Test Session/i })
      expect(selectedButton).toHaveAttribute("aria-current", "page")
      expect(selectedButton.className).toContain("border-blue-500")
      expect(selectedButton.className).toContain("bg-blue-50")
    })

    it("does not highlight non-selected sessions", () => {
      render(<SessionSidebar {...defaultProps} currentSessionId='session-1' />)

      // Get session buttons (exclude the header "新しいチャット" button)
      const buttons = screen.getAllByRole("button")
      const sessionButtons = buttons.filter((b) => b.closest("li"))
      const unselectedButton = sessionButtons.find((b) => !b.textContent?.includes("Test Session"))

      expect(unselectedButton).not.toHaveAttribute("aria-current")
    })
  })

  describe("interactions", () => {
    it("calls onNewSession when new chat button clicked", async () => {
      const user = userEvent.setup()
      const onNewSession = vi.fn()

      render(<SessionSidebar {...defaultProps} onNewSession={onNewSession} />)

      await user.click(screen.getByRole("button", { name: "新しいチャット" }))

      expect(onNewSession).toHaveBeenCalledTimes(1)
    })

    it("calls onSelectSession when session clicked", async () => {
      const user = userEvent.setup()
      const onSelectSession = vi.fn()

      render(<SessionSidebar {...defaultProps} onSelectSession={onSelectSession} />)

      await user.click(screen.getByText("Test Session"))

      expect(onSelectSession).toHaveBeenCalledWith("session-1")
    })

    it("calls onSelectSession with correct session id", async () => {
      const user = userEvent.setup()
      const onSelectSession = vi.fn()

      render(<SessionSidebar {...defaultProps} onSelectSession={onSelectSession} />)

      // Click the second session (with null title)
      const sessionButtons = screen.getAllByRole("button").filter((b) => b.closest("li"))
      const secondSession = sessionButtons[1]
      await user.click(secondSession)

      expect(onSelectSession).toHaveBeenCalledWith("session-2")
    })
  })

  describe("accessibility", () => {
    it("has accessible navigation landmark", () => {
      render(<SessionSidebar {...defaultProps} />)

      const nav = screen.getByRole("navigation", { name: "セッション一覧" })
      expect(nav).toBeInTheDocument()
    })

    it("uses semantic list structure", () => {
      render(<SessionSidebar {...defaultProps} />)

      expect(screen.getByRole("list")).toBeInTheDocument()
      expect(screen.getAllByRole("listitem")).toHaveLength(2)
    })
  })
})
