import { useEffect, useRef } from "react"
import MessageItem from "./MessageItem"
import type { Message, PipelineRun } from "./MessageItem"
import { Layers } from "lucide-react"

interface MessageListProps {
  messages: Message[]
  onSelectPipelineRun: (run: PipelineRun) => void
  selectedPipelineRunId: number | null
}

export default function MessageList({
  messages,
  onSelectPipelineRun,
  selectedPipelineRunId,
}: MessageListProps) {
  const containerRef = useRef<HTMLDivElement>(null)

  // Auto scroll to bottom
  useEffect(() => {
    if (containerRef.current) {
      containerRef.current.scrollTop = containerRef.current.scrollHeight
    }
  }, [messages])

  if (messages.length === 0) {
    return (
      <div className="flex-1 flex flex-col items-center justify-center p-8 select-none bg-primary/45 overflow-y-auto">
        <div className="w-full max-w-[640px] text-center space-y-8 my-auto">
          {/* Logo or Icon */}
          <div className="inline-flex h-16 w-16 items-center justify-center rounded-2xl bg-accent-soft border border-accent/20 text-accent">
            <Layers className="h-8 w-8" />
          </div>

          <div className="space-y-3">
            <h2 className="text-3xl font-semibold tracking-tight text-primary">
              AI Research Workbench
            </h2>
            <p className="text-[15px] text-secondary max-w-lg mx-auto">
              A specialized workspace for bio-medical graph extraction and reasoning traces. Ask a question to begin a pipeline run.
            </p>
          </div>
        </div>
      </div>
    )
  }

  return (
    <div ref={containerRef} className="flex-1 overflow-y-auto w-full">
      <div className="flex flex-col w-full pb-8">
        {messages.map((message) => (
          <MessageItem
            key={message.id}
            message={message}
            onSelectPipelineRun={onSelectPipelineRun}
            isSelectedRun={selectedPipelineRunId === message.pipeline_run?.id}
          />
        ))}
      </div>
    </div>
  )
}
