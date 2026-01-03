import { render, screen } from "@testing-library/react"
import userEvent from "@testing-library/user-event"
import { describe, expect, it, vi } from "vitest"
import { RAGChatInput } from "./RAGChatInput"

describe("RAGChatInput", () => {
  describe("rendering", () => {
    it("renders textarea and submit button", () => {
      render(<RAGChatInput onSubmit={vi.fn()} />)

      expect(screen.getByRole("textbox")).toBeInTheDocument()
      expect(screen.getByRole("button")).toBeInTheDocument()
    })

    it("shows placeholder text", () => {
      render(<RAGChatInput onSubmit={vi.fn()} />)

      expect(screen.getByPlaceholderText("質問を入力してください...")).toBeInTheDocument()
    })

    it("shows keyboard shortcut hint", () => {
      render(<RAGChatInput onSubmit={vi.fn()} />)

      expect(screen.getByText(/で送信$/)).toBeInTheDocument()
    })
  })

  describe("disabled state", () => {
    it("disables textarea when isDisabled is true", () => {
      render(<RAGChatInput onSubmit={vi.fn()} isDisabled />)

      expect(screen.getByRole("textbox")).toBeDisabled()
    })

    it("disables button when isDisabled is true", () => {
      render(<RAGChatInput onSubmit={vi.fn()} isDisabled />)

      expect(screen.getByRole("button")).toBeDisabled()
    })

    it("disables button when input is empty", () => {
      render(<RAGChatInput onSubmit={vi.fn()} />)

      expect(screen.getByRole("button")).toBeDisabled()
    })
  })

  describe("user interaction", () => {
    it("allows typing in textarea", async () => {
      const user = userEvent.setup()
      render(<RAGChatInput onSubmit={vi.fn()} />)

      const textarea = screen.getByRole("textbox")
      await user.type(textarea, "Hello")

      expect(textarea).toHaveValue("Hello")
    })

    it("enables button when text is entered", async () => {
      const user = userEvent.setup()
      render(<RAGChatInput onSubmit={vi.fn()} />)

      await user.type(screen.getByRole("textbox"), "Hello")

      expect(screen.getByRole("button")).not.toBeDisabled()
    })

    it("calls onSubmit when button is clicked", async () => {
      const user = userEvent.setup()
      const onSubmit = vi.fn()
      render(<RAGChatInput onSubmit={onSubmit} />)

      await user.type(screen.getByRole("textbox"), "Hello")
      await user.click(screen.getByRole("button"))

      expect(onSubmit).toHaveBeenCalledWith("Hello")
    })

    it("clears input after submission", async () => {
      const user = userEvent.setup()
      render(<RAGChatInput onSubmit={vi.fn()} />)

      const textarea = screen.getByRole("textbox")
      await user.type(textarea, "Hello")
      await user.click(screen.getByRole("button"))

      expect(textarea).toHaveValue("")
    })

    it("trims whitespace from message", async () => {
      const user = userEvent.setup()
      const onSubmit = vi.fn()
      render(<RAGChatInput onSubmit={onSubmit} />)

      await user.type(screen.getByRole("textbox"), "  Hello  ")
      await user.click(screen.getByRole("button"))

      expect(onSubmit).toHaveBeenCalledWith("Hello")
    })

    it("does not submit empty or whitespace-only input", async () => {
      const user = userEvent.setup()
      const onSubmit = vi.fn()
      render(<RAGChatInput onSubmit={onSubmit} />)

      await user.type(screen.getByRole("textbox"), "   ")
      // Button should be disabled for whitespace-only input

      expect(screen.getByRole("button")).toBeDisabled()
    })
  })

  describe("keyboard shortcuts", () => {
    it("submits on Ctrl+Enter", async () => {
      const user = userEvent.setup()
      const onSubmit = vi.fn()
      render(<RAGChatInput onSubmit={onSubmit} />)

      const textarea = screen.getByRole("textbox")
      await user.type(textarea, "Hello")
      await user.keyboard("{Control>}{Enter}{/Control}")

      expect(onSubmit).toHaveBeenCalledWith("Hello")
    })

    it("submits on Meta+Enter (Cmd)", async () => {
      const user = userEvent.setup()
      const onSubmit = vi.fn()
      render(<RAGChatInput onSubmit={onSubmit} />)

      const textarea = screen.getByRole("textbox")
      await user.type(textarea, "Hello")
      await user.keyboard("{Meta>}{Enter}{/Meta}")

      expect(onSubmit).toHaveBeenCalledWith("Hello")
    })

    it("does not submit on Enter alone", async () => {
      const user = userEvent.setup()
      const onSubmit = vi.fn()
      render(<RAGChatInput onSubmit={onSubmit} />)

      const textarea = screen.getByRole("textbox")
      await user.type(textarea, "Hello")
      await user.keyboard("{Enter}")

      expect(onSubmit).not.toHaveBeenCalled()
    })
  })
})
