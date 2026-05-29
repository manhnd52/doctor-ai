import { useState } from "react"
import { Bot, User, Check, Copy, ChevronRight, Layers, AlertCircle } from "lucide-react"
import { getStepDisplayName } from "../store/chatStore"

export interface PipelineStep {
  name: string
  status: "completed" | "failed" | "doing" | "pending"
  duration_ms?: number
  details?: string
}

export interface PipelineRun {
  id: number
  question: string
  query: string
  status: string
  trace_data?: {
    steps: PipelineStep[]
    question_type?: "PIPELINE" | "LLM"
  }
}

export interface Message {
  id: number
  role: "user" | "assistant"
  content: string
  created_at: string
  pipeline_run?: PipelineRun
}

interface MessageItemProps {
  message: Message
  onSelectPipelineRun: (run: PipelineRun) => void
  isSelectedRun: boolean
}

const getSteps = (run: any): any[] => {
  if (!run || !run.trace_data) return []
  const traceData = run.trace_data
  if (Array.isArray(traceData)) return traceData
  if (Array.isArray(traceData.steps)) return traceData.steps
  return []
}

const getQuestionType = (run: any): "PIPELINE" | "LLM" => {
  if (!run) return "LLM"
  const traceData = run.trace_data
  if (!traceData) return "LLM"
  if (traceData.question_type) return traceData.question_type
  const steps = getSteps(run)
  return steps.length > 0 ? "PIPELINE" : "LLM"
}

export default function MessageItem({
  message,
  onSelectPipelineRun,
  isSelectedRun,
}: MessageItemProps) {
  const isAssistant = message.role === "assistant"
  const isFailed = isAssistant && message.pipeline_run?.status === "failed"
  const steps = getSteps(message.pipeline_run)
  const qType = getQuestionType(message.pipeline_run)
  const hasPipeline = !!message.pipeline_run && qType === "PIPELINE"

  console.log("hasPipeline", hasPipeline, message.content)

  const [copiedCodeText, setCopiedCodeText] = useState<string | null>(null)

  const handleCopyCode = (code: string) => {
    navigator.clipboard.writeText(code)
    setCopiedCodeText(code)
    setTimeout(() => setCopiedCodeText(null), 2000)
  }

  // A simple custom parser for code blocks (```code```) and bold text (**bold**)
  const renderFormattedContent = (text: string) => {
    if (!text) return null

    const parts = text.split(/(```[\s\S]*?```)/g)

    return parts.map((part, index) => {
      // Check if it's a code block
      if (part.startsWith("```") && part.endsWith("```")) {
        const lines = part.slice(3, -3).trim().split("\n")
        let language = "code"
        let codeContent = lines.join("\n")

        // Check if first line is language specifier
        if (lines[0] && /^[a-zA-Z0-9_-]+$/.test(lines[0])) {
          language = lines[0]
          codeContent = lines.slice(1).join("\n")
        }

        return (
          <div key={index} className="my-4 overflow-hidden rounded-xl border border-theme bg-neutral-900 text-neutral-100">
            <div className="flex items-center justify-between bg-neutral-800 px-4 py-2 text-xs font-mono text-neutral-400 select-none">
              <span>{language.toUpperCase()}</span>
              <button
                onClick={() => handleCopyCode(codeContent)}
                className="flex items-center gap-1.5 hover:text-white transition"
              >
                {copiedCodeText === codeContent ? (
                  <>
                    <Check className="h-3 w-3 text-emerald-400" />
                    <span className="text-emerald-400">Copied</span>
                  </>
                ) : (
                  <>
                    <Copy className="h-3 w-3" />
                    <span>Copy</span>
                  </>
                )}
              </button>
            </div>
            <pre className="overflow-x-auto p-4 font-mono text-sm leading-relaxed">
              <code>{codeContent}</code>
            </pre>
          </div>
        )
      }

      // Handle paragraphs, lists and inline bolding inside plain text
      const inlineParts = part.split(/(\*\*.*?\*\*)/g)
      const parsedInline = inlineParts.map((subPart, subIdx) => {
        if (subPart.startsWith("**") && subPart.endsWith("**")) {
          return <strong key={subIdx} className="font-bold text-primary">{subPart.slice(2, -2)}</strong>
        }
        return subPart
      })

      return (
        <span key={index} className="whitespace-pre-wrap leading-relaxed">
          {parsedInline}
        </span>
      )
    })
  }

  return (
    <div className={`flex w-full py-2 justify-center`}>
      <div className={`flex w-full p-3 rounded-2xl max-w-[720px] items-start gap-4 px-4 sm:gap-6 ${isAssistant
        ? (isFailed
          ? "bg-red-500/5 border border-red-500/20"
          : "bg-primary")
        : "bg-secondary border border-theme"
        }`}>
        {/* Avatar */}
        <div className={`flex h-8 w-8 shrink-0 items-center justify-center rounded-lg shadow-sm border ${isAssistant
          ? (isFailed
            ? "bg-red-500/10 border-red-500/20 text-red-500"
            : "bg-accent/10 border-accent/20 text-accent")
          : "bg-neutral-100 border-neutral-200 text-neutral-600"
          }`}>
          {isAssistant ? (isFailed ? <AlertCircle className="h-4.5 w-4.5" /> : <Bot className="h-4.5 w-4.5" />) : <User className="h-4.5 w-4.5" />}
        </div>

        {/* Content Area */}
        <div className="flex-1 min-w-0 space-y-4">
          <div className={`text-sm font-semibold tracking-wide uppercase select-none ${isFailed ? "text-red-500" : "text-secondary"}`}>
            {isAssistant ? (isFailed ? "Assistant (Error)" : "Assistant") : "You"}
          </div>

          <div className={`text-[15px] ${isFailed ? "text-red-500 font-medium animate-pulse-once" : "text-primary"} space-y-2`}>
            {isFailed
              ? message.content || "An error occurred during execution."
              : renderFormattedContent(message.content)
            }
          </div>

          {/* Inline Pipeline Steps (Inspector summary) */}
          {isAssistant && hasPipeline && (
            <div className={`mt-4 rounded-2xl border p-4 transition-all shadow-[0_2px_12px_rgba(0,0,0,0.02)] ${isFailed
              ? "border-red-500/20 bg-red-500/5"
              : isSelectedRun
                ? "ring-1 ring-accent border-accent/60 bg-primary"
                : "border-theme bg-primary hover:border-neutral-300"
              }`}>
              <div className={`flex items-center justify-between pb-3 border-b mb-3 ${isFailed ? "border-red-500/20" : "border-theme/60"
                }`}>
                <div className="flex items-center gap-2 text-sm font-semibold text-primary">
                  <Layers className={`h-4 w-4 ${isFailed ? "text-red-500" : "text-accent"}`} />
                  <span className={isFailed ? "text-red-500" : ""}>Pipeline Inspector</span>
                </div>
                <button
                  onClick={() => onSelectPipelineRun(message.pipeline_run!)}
                  className={`flex items-center gap-1 text-xs font-semibold hover:underline transition ${isFailed ? "text-red-500" : "text-accent"
                    }`}
                >
                  {isSelectedRun ? "Inspecting" : "Inspect Run"}
                  <ChevronRight className="h-3 w-3" />
                </button>
              </div>

              {/* Steps List */}
              {steps.length > 0 && (
                <div className="grid grid-cols-1 sm:grid-cols-2 gap-2 text-xs">
                  {steps.map((step: any, idx: number) => {
                    const stepStatus = step.status || "completed"
                    const isStepFailed = stepStatus === "failed"
                    return (
                      <div
                        key={idx}
                        onClick={() => onSelectPipelineRun(message.pipeline_run!)}
                        className={`flex items-center justify-between rounded-lg border px-3 py-2 cursor-pointer transition ${isStepFailed
                          ? "border-red-500/20 bg-red-500/5 hover:bg-red-500/10"
                          : "border-theme bg-secondary/35 hover:bg-secondary"
                          }`}
                      >
                        <span className={`font-medium truncate mr-2 ${isStepFailed ? "text-red-500" : ""}`}>
                          {getStepDisplayName(step.name)}
                        </span>
                        <span className={`shrink-0 rounded px-1.5 py-0.5 text-[10px] font-bold uppercase tracking-wide ${isStepFailed
                          ? "bg-red-500/10 text-red-500"
                          : "bg-emerald-500/10 text-emerald-600"
                          }`}>
                          {isStepFailed ? "Failed" : "Done"}
                        </span>
                      </div>
                    )
                  })}
                </div>
              )}
            </div>
          )}
        </div>
      </div>
    </div>
  )
}
