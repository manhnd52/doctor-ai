import React, { useState, useRef, useEffect } from "react"
import { Send, Square } from "lucide-react"

interface InputBoxProps {
  onSendMessage: (content: string) => void
  onStopSendMessage?: () => void
  isSending?: boolean
  disabled?: boolean
  placeholder?: string
}

export default function InputBox({
  onSendMessage,
  onStopSendMessage,
  isSending = false,
  disabled = false,
  placeholder = "Type a medical question or ask about Neo4j graph...",
}: InputBoxProps) {
  const [content, setContent] = useState("")
  const textareaRef = useRef<HTMLTextAreaElement>(null)

  // Auto-resize height
  useEffect(() => {
    if (textareaRef.current) {
      textareaRef.current.style.height = "auto"
      textareaRef.current.style.height = `${Math.min(
        textareaRef.current.scrollHeight,
        200
      )}px`
    }
  }, [content])

  const handleSubmit = (e?: React.FormEvent) => {
    if (e) e.preventDefault()
    if (content.trim() && !disabled) {
      onSendMessage(content.trim())
      setContent("")
    }
  }

  const handleKeyDown = (e: React.KeyboardEvent<HTMLTextAreaElement>) => {
    if (e.key === "Enter" && !e.shiftKey) {
      e.preventDefault()
      handleSubmit()
    }
  }

  return (
    <div className="sticky top-0 bg-primary/95 backdrop-blur-md border-t border-theme p-4 w-full flex justify-center z-20">
      <form
        onSubmit={handleSubmit}
        className="w-full max-w-[720px] flex items-end gap-2 border border-theme rounded-[24px] bg-secondary/35 px-4 py-2.5 shadow-sm transition-all focus-within:border-accent focus-within:ring-1 focus-within:ring-accent/20"
      >
        <textarea
          ref={textareaRef}
          rows={1}
          value={content}
          onChange={(e) => setContent(e.target.value)}
          onKeyDown={handleKeyDown}
          placeholder={placeholder}
          disabled={disabled || isSending}
          className="flex-1 bg-transparent resize-none outline-none py-1 text-sm text-primary max-h-[200px] placeholder:text-muted"
          style={{ minHeight: "24px" }}
        />
        {isSending ? (
          <button
            type="button"
            onClick={() => {
              onStopSendMessage?.();
            }}
            className="shrink-0 flex h-8 w-8 items-center justify-center rounded-full bg-red-500 hover:bg-red-600 text-white transition active:scale-95 cursor-pointer"
            title="Stop generating"
          >
            <Square className="h-3.5 w-3.5 fill-white" />
          </button>
        ) : (
          <button
            type="submit"
            disabled={!content.trim() || disabled}
            className={`shrink-0 flex h-8 w-8 items-center justify-center rounded-full transition active:scale-95 ${content.trim() && !disabled
              ? "bg-accent text-black hover:brightness-110"
              : "bg-secondary text-muted cursor-not-allowed"
              }`}
          >
            <Send className="h-4 w-4" />
          </button>
        )}
      </form>
    </div>
  )
}
