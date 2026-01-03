import { ChevronDown, ChevronUp, FileText } from "lucide-react"
import { useEffect, useRef, useState } from "react"
import type { ChatMessage, SourceInfo } from "../store"

type RAGChatHistoryProps = {
  messages: readonly ChatMessage[]
  currentResponse: string
  isStreaming: boolean
}

function SourcesPanel({ sources }: { sources: SourceInfo[] }) {
  const [isOpen, setIsOpen] = useState(false)

  if (sources.length === 0) return null

  return (
    <div className='mt-2 border-t border-gray-200 pt-2'>
      <button
        type='button'
        onClick={() => setIsOpen(!isOpen)}
        className='flex items-center gap-1 text-xs text-gray-500 hover:text-gray-700'
      >
        <FileText size={12} />
        <span>参照文書 ({sources.length})</span>
        {isOpen ? <ChevronUp size={12} /> : <ChevronDown size={12} />}
      </button>
      {isOpen && (
        <div className='mt-2 space-y-1'>
          {sources.map((source, index) => (
            <div
              key={`${source.filename}-${source.page}-${index}`}
              className='rounded bg-gray-50 px-2 py-1 text-xs text-gray-600'
            >
              <span className='font-medium'>{source.filename}</span>
              {source.page && <span className='ml-2'>p.{source.page}</span>}
              {source.slide && <span className='ml-2'>slide {source.slide}</span>}
              {source.sheet && <span className='ml-2'>{source.sheet}</span>}
              <span className='ml-2 text-gray-400'>
                (score: {(source.score * 100).toFixed(1)}%)
              </span>
            </div>
          ))}
        </div>
      )}
    </div>
  )
}

export function RAGChatHistory({ messages, currentResponse, isStreaming }: RAGChatHistoryProps) {
  const scrollRef = useRef<HTMLDivElement>(null)

  // Auto-scroll when messages change or streaming content updates
  // biome-ignore lint/correctness/useExhaustiveDependencies: intentional scroll trigger
  useEffect(() => {
    scrollRef.current?.scrollTo({
      top: scrollRef.current.scrollHeight,
      behavior: "smooth",
    })
  }, [messages.length, currentResponse])

  if (messages.length === 0 && !isStreaming) {
    return (
      <div className='flex h-full items-center justify-center p-8 text-center text-gray-400'>
        <div>
          <p className='mb-2 text-lg'>RAG Chat</p>
          <p className='text-sm'>
            質問を入力して
            <br />
            文書に基づいた回答を得ましょう
          </p>
        </div>
      </div>
    )
  }

  return (
    <div ref={scrollRef} className='h-full space-y-4 overflow-y-auto p-4'>
      {messages.map((msg) => (
        <div
          key={msg.id}
          className={`rounded-lg p-3 ${
            msg.role === "user" ? "ml-8 bg-blue-50 text-blue-900" : "mr-8 bg-gray-100 text-gray-900"
          }`}
        >
          <p className='whitespace-pre-wrap text-sm'>{msg.content}</p>
          {msg.sources && <SourcesPanel sources={msg.sources} />}
          <p className='mt-1 text-xs text-gray-400'>
            {msg.timestamp.toLocaleTimeString("ja-JP", {
              hour: "2-digit",
              minute: "2-digit",
            })}
          </p>
        </div>
      ))}

      {/* Streaming response */}
      {isStreaming && currentResponse && (
        <div className='mr-8 rounded-lg bg-gray-100 p-3 text-gray-900'>
          <p className='whitespace-pre-wrap text-sm'>{currentResponse}</p>
          <span className='inline-block animate-pulse'>▋</span>
        </div>
      )}
    </div>
  )
}
