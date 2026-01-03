import { useEffect, useSyncExternalStore } from "react"
import { RAGChatPanel } from "./components/RAGChatPanel"
import { SessionSidebar } from "./components/SessionSidebar"
import { RAGStore } from "./store"

// API URL: empty for same-origin (Docker Compose), or explicit URL
const apiUrl = import.meta.env.VITE_API_URL ?? ""

// Create store at module level
const ragStore = RAGStore.create(apiUrl)

export function App() {
  const snapshot = useSyncExternalStore(ragStore.subscribe, ragStore.getSnapshot)

  // Load sessions on mount
  useEffect(() => {
    ragStore.loadSessions()
  }, [])

  function handleSubmit(message: string) {
    ragStore.sendMessage(message)
  }

  function handleSelectSession(sessionId: string) {
    ragStore.selectSession(sessionId)
  }

  function handleNewSession() {
    ragStore.startNewSession()
  }

  return (
    <div className='flex h-screen overflow-hidden bg-gray-50'>
      {/* Session Sidebar */}
      <SessionSidebar
        sessions={snapshot.sessions}
        currentSessionId={snapshot.sessionId}
        isLoading={snapshot.isLoadingSessions}
        onSelectSession={handleSelectSession}
        onNewSession={handleNewSession}
      />

      {/* Main Chat Panel */}
      <div className='flex flex-1 flex-col bg-white'>
        {/* Header */}
        <header className='border-b border-gray-200 bg-white px-6 py-4'>
          <h1 className='text-xl font-semibold text-gray-900'>RAG Chat</h1>
          <p className='mt-1 text-sm text-gray-500'>文書に基づいて質問に回答します</p>
          {snapshot.model && (
            <p className='mt-1 text-xs text-gray-400'>
              Model: {snapshot.model} ({snapshot.provider})
            </p>
          )}
        </header>

        {/* Chat Panel */}
        <div className='flex-1 overflow-hidden'>
          <RAGChatPanel
            messages={snapshot.messages}
            currentResponse={snapshot.currentResponse}
            isStreaming={snapshot.isStreaming}
            onSubmit={handleSubmit}
          />
        </div>

        {/* Error Display */}
        {snapshot.error && (
          <div className='border-t border-red-200 bg-red-50 px-6 py-3'>
            <p className='text-sm text-red-700'>
              <span className='font-medium'>エラー:</span> {snapshot.error.message}
            </p>
            <button
              type='button'
              onClick={() => ragStore.clearError()}
              className='mt-1 text-xs text-red-600 underline hover:text-red-800'
            >
              閉じる
            </button>
          </div>
        )}
      </div>
    </div>
  )
}
