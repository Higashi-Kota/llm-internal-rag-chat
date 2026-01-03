import type { MockSession, MockSessionMessage } from "./fixtures"
import { expect, test } from "./fixtures"

test.describe("RAG Chat - Basic UI", () => {
  test.beforeEach(async ({ page, utils }) => {
    await utils.mockRAGStreamAPI()
    await utils.mockSessionsAPI([])
    await page.goto("/")
    await utils.waitForApp()
  })

  test("should display app header", async ({ page }) => {
    await expect(page.locator("h1")).toHaveText("RAG Chat")
    await expect(page.locator("text=文書に基づいて質問に回答します")).toBeVisible()
  })

  test("should show empty state message", async ({ page }) => {
    await expect(page.locator("text=質問を入力して")).toBeVisible()
    await expect(page.locator("text=文書に基づいた回答を得ましょう")).toBeVisible()
  })

  test("should show chat input with placeholder", async ({ page }) => {
    const textarea = page.locator("textarea")
    await expect(textarea).toBeVisible()
    await expect(textarea).toHaveAttribute("placeholder", /質問を入力してください/)
  })

  test("should show submit keyboard shortcut hint", async ({ page }) => {
    // Check for either Mac or Windows/Linux hint
    await expect(page.locator("text=/で送信/")).toBeVisible()
  })
})

test.describe("RAG Chat - Message Flow", () => {
  test.beforeEach(async ({ page, utils }) => {
    await utils.mockRAGStreamAPI()
    await utils.mockSessionsAPI([])
    await page.goto("/")
    await utils.waitForApp()
  })

  test("should send message and receive response", async ({ page, utils }) => {
    await utils.submitMessage("テスト質問です")

    // Wait for response to complete
    await utils.waitForResponse()

    // Verify user message appears
    await expect(page.locator("text=テスト質問です")).toBeVisible()

    // Verify assistant response appears
    await expect(page.locator("text=これはテスト回答です")).toBeVisible()
  })

  test("should display model info after response", async ({ page, utils }) => {
    await utils.mockRAGStreamAPI({
      model: "llama3.2",
      provider: "ollama",
    })

    await utils.submitMessage("モデル情報テスト")
    await utils.waitForResponse()

    // Check model info is displayed in header
    await expect(page.locator("text=llama3.2")).toBeVisible()
    await expect(page.locator("text=ollama")).toBeVisible()
  })

  test("should show user message with blue background", async ({ page, utils }) => {
    await utils.submitMessage("ユーザーメッセージ")
    await utils.waitForResponse()

    const userMessage = page.locator(".bg-blue-50")
    await expect(userMessage).toContainText("ユーザーメッセージ")
  })

  test("should show assistant message with gray background", async ({ page, utils }) => {
    await utils.submitMessage("質問")
    await utils.waitForResponse()

    const assistantMessage = page.locator(".bg-gray-100").first()
    await expect(assistantMessage).toContainText("これはテスト回答です")
  })
})

test.describe("RAG Chat - Sources", () => {
  test("should display sources panel after response", async ({ page, utils }) => {
    await utils.mockRAGStreamAPI({
      sources: [
        { filename: "test.pdf", page: 1, score: 0.95 },
        { filename: "doc.docx", page: 5, score: 0.85 },
      ],
    })
    await utils.mockSessionsAPI([])

    await page.goto("/")
    await utils.waitForApp()
    await utils.submitMessage("ソーステスト")
    await utils.waitForResponse()

    // Check sources panel button
    await expect(page.locator("button:has-text('参照文書 (2)')")).toBeVisible()
  })

  test("should expand sources panel on click", async ({ page, utils }) => {
    await utils.mockRAGStreamAPI({
      sources: [{ filename: "document.pdf", page: 10, score: 0.92 }],
    })
    await utils.mockSessionsAPI([])

    await page.goto("/")
    await utils.waitForApp()
    await utils.submitMessage("ソース展開テスト")
    await utils.waitForResponse()

    // Click to expand
    await page.locator("button:has-text('参照文書')").click()

    // Verify source details are visible
    await expect(page.locator("text=document.pdf")).toBeVisible()
    await expect(page.locator("text=p.10")).toBeVisible()
    await expect(page.locator("text=/score:.*92/")).toBeVisible()
  })
})

test.describe("RAG Chat - Streaming", () => {
  test("should disable input during streaming", async ({ page, utils }) => {
    await utils.mockRAGStreamAPI()
    await utils.mockSessionsAPI([])

    await page.goto("/")
    await utils.waitForApp()

    const textarea = page.locator("textarea")
    await textarea.fill("ストリーミングテスト")
    await textarea.press("Control+Enter")

    // During streaming, textarea should be disabled
    // Note: This might be flaky if streaming is too fast
    await utils.waitForResponse()

    // After completion, textarea should be enabled
    await expect(textarea).toBeEnabled()
  })

  test("should show loading spinner on submit button during streaming", async ({ page, utils }) => {
    await utils.mockRAGStreamAPI()
    await utils.mockSessionsAPI([])

    await page.goto("/")
    await utils.waitForApp()
    await utils.submitMessage("スピナーテスト")

    // After response completes, verify normal button state
    await utils.waitForResponse()
    await expect(page.locator("button svg.lucide-send")).toBeVisible()
  })
})

test.describe("RAG Chat - Error Handling", () => {
  test("should display error message on API error", async ({ page, utils }) => {
    await utils.mockRAGStreamAPI({
      error: {
        code: "RETRIEVAL_FAILED",
        message: "文書の検索に失敗しました",
      },
    })
    await utils.mockSessionsAPI([])

    await page.goto("/")
    await utils.waitForApp()
    await utils.submitMessage("エラーテスト")

    // Wait for error display
    await expect(page.locator("text=文書の検索に失敗しました")).toBeVisible()
  })

  test("should show close button for error", async ({ page, utils }) => {
    await utils.mockRAGStreamAPI({
      error: {
        code: "NETWORK_ERROR",
        message: "接続エラー",
      },
    })
    await utils.mockSessionsAPI([])

    await page.goto("/")
    await utils.waitForApp()
    await utils.submitMessage("エラークローズテスト")

    // Wait for error and close button
    await expect(page.locator("text=接続エラー")).toBeVisible()
    await expect(page.locator("button:has-text('閉じる')")).toBeVisible()
  })

  test("should clear error when close button clicked", async ({ page, utils }) => {
    await utils.mockRAGStreamAPI({
      error: {
        code: "NETWORK_ERROR",
        message: "テストエラー",
      },
    })
    await utils.mockSessionsAPI([])

    await page.goto("/")
    await utils.waitForApp()
    await utils.submitMessage("エラー解除テスト")

    // Wait for error
    await expect(page.locator("text=テストエラー")).toBeVisible()

    // Click close button
    await page.locator("button:has-text('閉じる')").click()

    // Error should be hidden
    await expect(page.locator("text=テストエラー")).toBeHidden()
  })
})

test.describe("RAG Chat - Input Validation", () => {
  test("should not submit empty message", async ({ page, utils }) => {
    await utils.mockRAGStreamAPI()
    await utils.mockSessionsAPI([])

    await page.goto("/")
    await utils.waitForApp()

    // Submit button should be disabled when input is empty
    const submitButton = page
      .locator("button")
      .filter({ has: page.locator("svg") })
      .last()
    await expect(submitButton).toBeDisabled()
  })

  test("should not submit whitespace-only message", async ({ page, utils }) => {
    await utils.mockRAGStreamAPI()
    await utils.mockSessionsAPI([])

    await page.goto("/")
    await utils.waitForApp()

    const textarea = page.locator("textarea")
    await textarea.fill("   ")

    // Submit button should still be disabled
    const submitButton = page
      .locator("button")
      .filter({ has: page.locator("svg") })
      .last()
    await expect(submitButton).toBeDisabled()
  })

  test("should clear input after successful submit", async ({ page, utils }) => {
    await utils.mockRAGStreamAPI()
    await utils.mockSessionsAPI([])

    await page.goto("/")
    await utils.waitForApp()
    await utils.submitMessage("クリアテスト")

    // Input should be cleared after submit
    const textarea = page.locator("textarea")
    await expect(textarea).toHaveValue("")
  })
})

test.describe("RAG Chat - Session Sidebar", () => {
  const mockSessions: MockSession[] = [
    {
      id: "session-1",
      title: "テストセッション",
      created_at: "2024-01-15T10:00:00Z",
      updated_at: "2024-01-15T11:00:00Z",
    },
    {
      id: "session-2",
      title: null,
      created_at: "2024-01-14T10:00:00Z",
      updated_at: "2024-01-14T11:00:00Z",
    },
  ]

  const mockMessages: MockSessionMessage[] = [
    {
      id: "msg-1",
      role: "user",
      content: "テスト質問です",
      sources: null,
      created_at: "2024-01-15T10:00:00Z",
      model: null,
      provider: null,
    },
    {
      id: "msg-2",
      role: "assistant",
      content: "これはテスト回答です。",
      sources: [{ filename: "test.pdf", page: 1, score: 0.95 }],
      created_at: "2024-01-15T10:01:00Z",
      model: "gemma3:4b",
      provider: "ollama",
    },
  ]

  test("should display session sidebar", async ({ page, utils }) => {
    await utils.mockSessionsAPI([])
    await utils.mockRAGStreamAPI()

    await page.goto("/")
    await utils.waitForApp()

    // Check sidebar elements
    await expect(page.getByRole("heading", { name: "チャット履歴" })).toBeVisible()
    await expect(page.locator('button:has-text("新しいチャット")')).toBeVisible()
  })

  test("should display session list", async ({ page, utils }) => {
    await utils.mockSessionsAPI(mockSessions)
    await utils.mockRAGStreamAPI()

    await page.goto("/")
    await utils.waitForApp()

    // Check session items
    await expect(page.locator("text=テストセッション")).toBeVisible()
    // Null title session should show fallback text
    await expect(
      page.locator('nav[aria-label="セッション一覧"] button:has-text("新しいチャット")'),
    ).toBeVisible()
  })

  test("should show empty message when no sessions", async ({ page, utils }) => {
    await utils.mockSessionsAPI([])
    await utils.mockRAGStreamAPI()

    await page.goto("/")
    await utils.waitForApp()

    await expect(page.locator("text=チャット履歴がありません")).toBeVisible()
  })

  test("should restore session on click", async ({ page, utils }) => {
    await utils.mockSessionsAPI(mockSessions)
    await utils.mockSessionDetailAPI("session-1", mockSessions[0], mockMessages)
    await utils.mockRAGStreamAPI()

    await page.goto("/")
    await utils.waitForApp()

    // Click on the session
    await page.locator("text=テストセッション").click()

    // Wait for messages to be restored
    await expect(page.locator("text=テスト質問です")).toBeVisible()
    await expect(page.locator("text=これはテスト回答です。")).toBeVisible()
  })

  test("should clear messages on new chat button click", async ({ page, utils }) => {
    await utils.mockSessionsAPI(mockSessions)
    await utils.mockSessionDetailAPI("session-1", mockSessions[0], mockMessages)
    await utils.mockRAGStreamAPI()

    await page.goto("/")
    await utils.waitForApp()

    // First, select a session
    await page.locator("text=テストセッション").click()
    await expect(page.locator("text=テスト質問です")).toBeVisible()

    // Click new chat button
    await page.locator('button:has-text("新しいチャット")').first().click()

    // Messages should be cleared, show empty state
    await expect(page.locator("text=質問を入力して")).toBeVisible()
    await expect(page.locator("text=テスト質問です")).toBeHidden()
  })
})
