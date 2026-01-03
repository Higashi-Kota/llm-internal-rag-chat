import type { ChatMessage } from "../store"
import { RAGChatHistory } from "./RAGChatHistory"
import { RAGChatInput } from "./RAGChatInput"

type RAGChatPanelProps = {
  messages: readonly ChatMessage[]
  currentResponse: string
  isStreaming: boolean
  onSubmit: (message: string) => void
}

export function RAGChatPanel({
  messages,
  currentResponse,
  isStreaming,
  onSubmit,
}: RAGChatPanelProps) {
  return (
    <div className='flex h-full flex-col'>
      {/* Chat history */}
      <div className='flex-1 overflow-hidden'>
        <RAGChatHistory
          messages={messages}
          currentResponse={currentResponse}
          isStreaming={isStreaming}
        />
      </div>

      {/* Input */}
      <RAGChatInput onSubmit={onSubmit} isDisabled={isStreaming} />
    </div>
  )
}
