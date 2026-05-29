import { useEffect, useRef } from "react"
import MessageItem from "./MessageItem"
import type { Message, PipelineRun } from "./MessageItem"
import { Layers, Database, Cpu, Compass } from "lucide-react"

interface MessageListProps {
  messages: Message[]
  onSelectPipelineRun: (run: PipelineRun) => void
  selectedPipelineRunId: number | null
  onSuggestionClick?: (content: string) => void
}

export default function MessageList({
  messages,
  onSelectPipelineRun,
  selectedPipelineRunId,
  onSuggestionClick,
}: MessageListProps) {
  const containerRef = useRef<HTMLDivElement>(null)

  // Auto scroll to bottom
  useEffect(() => {
    if (containerRef.current) {
      containerRef.current.scrollTop = containerRef.current.scrollHeight
    }
  }, [messages])

  if (messages.length === 0) {
    const suggestions = [
      {
        icon: <Database className="h-5 w-5 text-accent" />,
        title: "Neo4j Retrieval",
        desc: "Explain how disease node attributes retrieve treatments in the graph.",
        prompt: "Show me how disease node attributes retrieve treatments in the graph."
      },
      {
        icon: <Cpu className="h-5 w-5 text-indigo-500" />,
        title: "Cypher Generation",
        desc: "Explain Cypher query generation for compound contraindications.",
        prompt: "How does the pipeline generate Cypher to find compound contraindications?"
      },
      {
        icon: <Compass className="h-5 w-5 text-sky-500" />,
        title: "Pipeline Walkthrough",
        desc: "Walk me through UMLS entity linking and evidence ranking steps.",
        prompt: "Can you explain the entity linking and evidence ranking steps in the pipeline?"
      }
    ]

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

          {/* Suggestion Cards */}
          <div className="grid grid-cols-1 gap-4 pt-4 text-left">
            {suggestions.map((card, idx) => (
              <div
                key={idx}
                onClick={() => onSuggestionClick && onSuggestionClick(card.prompt)}
                className="flex gap-4 rounded-2xl border border-theme bg-primary p-4 cursor-pointer hover:bg-secondary transition active:scale-[0.99] shadow-sm hover:border-neutral-300"
              >
                <div className="mt-0.5">{card.icon}</div>
                <div>
                  <h4 className="text-sm font-semibold text-primary">{card.title}</h4>
                  <p className="text-xs text-secondary mt-1">{card.desc}</p>
                </div>
              </div>
            ))}
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
