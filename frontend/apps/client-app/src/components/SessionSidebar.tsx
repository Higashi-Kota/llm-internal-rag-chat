import type { SessionSummary } from "../store/RAGStore"

interface SessionSidebarProps {
  readonly sessions: SessionSummary[]
  readonly currentSessionId: string | null
  readonly isLoading: boolean
  readonly onSelectSession: (id: string) => void
  readonly onNewSession: () => void
}

/**
 * Format date to relative string (今日, 昨日, or YYYY/MM/DD)
 */
function formatDate(dateStr: string): string {
  const date = new Date(dateStr)
  const now = new Date()
  const today = new Date(now.getFullYear(), now.getMonth(), now.getDate())
  const yesterday = new Date(today.getTime() - 24 * 60 * 60 * 1000)
  const targetDate = new Date(date.getFullYear(), date.getMonth(), date.getDate())

  if (targetDate.getTime() === today.getTime()) {
    return `今日 ${date.toLocaleTimeString("ja-JP", { hour: "2-digit", minute: "2-digit" })}`
  }
  if (targetDate.getTime() === yesterday.getTime()) {
    return `昨日 ${date.toLocaleTimeString("ja-JP", { hour: "2-digit", minute: "2-digit" })}`
  }
  return date.toLocaleDateString("ja-JP", { year: "numeric", month: "2-digit", day: "2-digit" })
}

export function SessionSidebar({
  sessions,
  currentSessionId,
  isLoading,
  onSelectSession,
  onNewSession,
}: SessionSidebarProps) {
  return (
    <aside className='flex h-full w-64 flex-col border-r border-gray-200 bg-gray-50'>
      {/* Header */}
      <header className='border-b border-gray-200 px-4 py-3'>
        <h2 className='text-sm font-semibold text-gray-700'>チャット履歴</h2>
      </header>

      {/* New Chat Button */}
      <div className='border-b border-gray-200 p-3'>
        <button
          type='button'
          onClick={onNewSession}
          className='flex w-full items-center justify-center gap-2 rounded-md border border-gray-300 bg-white px-4 py-2 text-sm font-medium text-gray-700 transition-colors hover:bg-gray-100 focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-blue-500'
        >
          <svg
            className='h-4 w-4'
            fill='none'
            stroke='currentColor'
            viewBox='0 0 24 24'
            aria-hidden='true'
          >
            <path strokeLinecap='round' strokeLinejoin='round' strokeWidth={2} d='M12 4v16m8-8H4' />
          </svg>
          新しいチャット
        </button>
      </div>

      {/* Session List */}
      <nav className='flex-1 overflow-y-auto' aria-label='セッション一覧'>
        {isLoading ? (
          <div className='flex items-center justify-center py-8'>
            <div className='h-5 w-5 animate-spin rounded-full border-2 border-gray-300 border-t-blue-500' />
          </div>
        ) : sessions.length === 0 ? (
          <div className='px-4 py-8 text-center text-sm text-gray-500'>
            チャット履歴がありません
          </div>
        ) : (
          <ul className='divide-y divide-gray-200'>
            {sessions.map((session) => {
              const isSelected = session.id === currentSessionId
              return (
                <li key={session.id}>
                  <button
                    type='button'
                    onClick={() => onSelectSession(session.id)}
                    className={`w-full px-4 py-3 text-left transition-colors focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-inset focus-visible:ring-blue-500 ${
                      isSelected ? "border-l-2 border-blue-500 bg-blue-50" : "hover:bg-gray-100"
                    }`}
                    aria-current={isSelected ? "page" : undefined}
                  >
                    <div className='truncate text-sm font-medium text-gray-900'>
                      {session.title ?? "新しいチャット"}
                    </div>
                    <div className='mt-1 text-xs text-gray-400'>
                      {formatDate(session.updatedAt)}
                    </div>
                  </button>
                </li>
              )
            })}
          </ul>
        )}
      </nav>
    </aside>
  )
}
