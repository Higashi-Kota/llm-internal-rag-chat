import { Loader2, Send } from "lucide-react"
import { useRef, useState } from "react"

type RAGChatInputProps = {
  onSubmit: (message: string) => void
  isDisabled?: boolean
}

export function RAGChatInput({ onSubmit, isDisabled }: RAGChatInputProps) {
  const [value, setValue] = useState("")
  const textareaRef = useRef<HTMLTextAreaElement>(null)

  function handleSubmit() {
    const trimmed = value.trim()
    if (trimmed && !isDisabled) {
      onSubmit(trimmed)
      setValue("")
    }
  }

  function handleKeyDown(e: React.KeyboardEvent<HTMLTextAreaElement>) {
    // Mod+Enter to submit (Cmd on Mac, Ctrl on others)
    if (e.key === "Enter" && (e.metaKey || e.ctrlKey)) {
      e.preventDefault()
      handleSubmit()
    }
  }

  const isMac = typeof navigator !== "undefined" && navigator.platform.includes("Mac")
  const submitHint = isMac ? "⌘ + Enter" : "Ctrl + Enter"

  return (
    <div className='border-t border-gray-200 bg-white p-4'>
      <div className='flex gap-3'>
        <textarea
          ref={textareaRef}
          value={value}
          onChange={(e) => setValue(e.target.value)}
          onKeyDown={handleKeyDown}
          className='flex-1 resize-none rounded-lg border border-gray-300 p-3 text-sm focus:border-blue-500 focus:outline-none focus:ring-2 focus:ring-blue-500/20 disabled:bg-gray-50 disabled:text-gray-500'
          placeholder='質問を入力してください...'
          rows={3}
          disabled={isDisabled}
        />
        <button
          type='button'
          onClick={handleSubmit}
          disabled={isDisabled || !value.trim()}
          className='self-end rounded-lg bg-blue-500 p-3 text-white transition-colors hover:bg-blue-600 disabled:cursor-not-allowed disabled:bg-gray-300'
        >
          {isDisabled ? <Loader2 size={20} className='animate-spin' /> : <Send size={20} />}
        </button>
      </div>
      <p className='mt-2 text-xs text-gray-500'>{submitHint} で送信</p>
    </div>
  )
}
