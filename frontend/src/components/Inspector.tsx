import { useState } from "react"
import { X, Layers, Clock, CheckCircle2, ChevronDown, ChevronUp, AlertCircle } from "lucide-react"
import type { PipelineRun, PipelineStep } from "./MessageItem"
import { getStepDisplayName } from "../store/chatStore"

interface InspectorProps {
  pipelineRun: PipelineRun | null
  onClose: () => void
}

const getSteps = (run: any): any[] => {
  if (!run || !run.trace_data) return []
  const traceData = run.trace_data
  if (Array.isArray(traceData)) return traceData
  if (Array.isArray(traceData.steps)) return traceData.steps
  return []
}

export default function Inspector({ pipelineRun, onClose }: InspectorProps) {
  const [expandedSteps, setExpandedSteps] = useState<Record<number, boolean>>({
    0: true, // Expand first step by default
  })

  const toggleStep = (idx: number) => {
    setExpandedSteps((prev) => ({
      ...prev,
      [idx]: !prev[idx],
    }))
  }

  const steps = getSteps(pipelineRun)

  // Calculate total latency
  const totalDuration = steps.reduce(
    (acc, step) => acc + (step.duration_ms || step.duration || 0),
    0
  )

  const formatStepDetailsText = (step: any): string => {
    if (step.details) return step.details
    if (step.output) {
      try {
        if (step.name === "answer_generation" && step.output.answer) {
          return `Synthesized Answer:\n${step.output.answer}`
        }
        return JSON.stringify(step.output, null, 2)
      } catch {
        return "No details provided for this step."
      }
    }
    return "No details provided for this step."
  }

  return (
    <div className="flex h-full w-[320px] flex-col border-l border-theme bg-panel text-primary select-none sm:w-[360px] md:w-[380px] shrink-0">
      {/* Header */}
      <div className="flex items-center justify-between border-b border-theme p-4">
        <div className="flex items-center gap-2">
          <Layers className="h-4.5 w-4.5 text-accent" />
          <h2 className="text-lg font-semibold tracking-tight">Inspector</h2>
        </div>
        <button
          onClick={onClose}
          className="inline-flex h-8 w-8 items-center justify-center rounded-lg hover:bg-secondary transition active:scale-95 text-secondary hover:text-primary"
        >
          <X className="h-4 w-4" />
        </button>
      </div>

      {/* Main Content */}
      <div className="flex-1 overflow-y-auto p-4 space-y-4">
        {pipelineRun ? (
          <>
            {/* Overview Card */}
            <div className={`rounded-2xl border p-4 space-y-3 ${
              pipelineRun.status === "failed" 
                ? "border-red-500/20 bg-red-500/5 text-red-500" 
                : "border-theme bg-secondary/35"
            }`}>
              <div className="flex justify-between items-center">
                <span className={`text-xs font-semibold uppercase ${pipelineRun.status === "failed" ? "text-red-500" : "text-secondary"}`}>Pipeline Status</span>
                <span className={`rounded px-2 py-0.5 text-[11px] font-bold uppercase tracking-wider ${
                  pipelineRun.status === "failed"
                    ? "bg-red-500/10 text-red-500"
                    : "bg-emerald-500/10 text-emerald-600"
                }`}>
                  {pipelineRun.status}
                </span>
              </div>
              <div className="flex items-center gap-2 font-medium text-sm">
                <Clock className={`h-4 w-4 ${pipelineRun.status === "failed" ? "text-red-500" : "text-muted"}`} />
                <span>Total execution: {totalDuration}ms</span>
              </div>
            </div>

            {/* Step Trace Title */}
            <h3 className="text-xs font-bold text-secondary uppercase tracking-[0.2em] px-1">
              Trace Execution
            </h3>

            {/* List of Steps */}
            <div className="space-y-3">
              {steps.map((step: any, idx: number) => {
                const isExpanded = !!expandedSteps[idx]
                const stepStatus = step.status || "completed"
                const isPending = stepStatus === "pending"
                const isDoing = stepStatus === "doing"
                const isFailed = stepStatus === "failed"

                return (
                  <div
                    key={idx}
                    className={`rounded-2xl border transition-all ${
                      isPending
                        ? "border-theme/40 opacity-55 bg-transparent"
                        : isFailed
                          ? "border-red-500/20 bg-red-500/5 shadow-sm"
                          : isExpanded
                            ? "border-accent/30 bg-primary shadow-sm"
                            : "border-theme bg-secondary/20 hover:border-neutral-300"
                    }`}
                  >
                    {/* Step Card Header */}
                    <div
                      onClick={() => !isPending && toggleStep(idx)}
                      className={`flex items-start justify-between p-3.5 ${!isPending ? "cursor-pointer select-none" : "cursor-not-allowed"
                        }`}
                    >
                      <div className="space-y-1 pr-2">
                        <div className="flex items-center gap-2">
                          {isFailed ? (
                            <AlertCircle className="h-4 w-4 text-red-500 shrink-0" />
                          ) : !isPending && !isDoing ? (
                            <CheckCircle2 className="h-4 w-4 text-emerald-500 shrink-0" />
                          ) : isDoing ? (
                            <div className="h-4.5 w-4.5 rounded-full border-2 border-accent border-t-transparent animate-spin shrink-0" />
                          ) : (
                            <div className="h-4 w-4 rounded-full border border-dashed border-neutral-400 shrink-0" />
                          )}
                          <h4 className={`text-sm font-semibold ${isFailed ? "text-red-500" : "text-primary"}`}>
                            {getStepDisplayName(step.name)}
                          </h4>
                        </div>
                        {(step.duration_ms !== undefined || step.duration !== undefined) && (
                          <p className="text-xs text-muted pl-6">
                            Duration: {step.duration_ms ?? step.duration}ms
                          </p>
                        )}
                      </div>

                      <div className="flex items-center gap-1.5 shrink-0 pl-1">
                        {stepStatus === "completed" && (
                          <span className="rounded bg-emerald-500/10 px-1.5 py-0.5 text-[9px] font-bold text-emerald-600 uppercase tracking-wide">
                            Done
                          </span>
                        )}
                        {isDoing && (
                          <span className="rounded bg-accent/10 px-1.5 py-0.5 text-[9px] font-bold text-accent uppercase tracking-wide animate-pulse">
                            Doing
                          </span>
                        )}
                        {isFailed && (
                          <span className="rounded bg-red-500/10 px-1.5 py-0.5 text-[9px] font-bold text-red-500 uppercase tracking-wide">
                            Failed
                          </span>
                        )}
                        {!isPending && (
                          <div className="text-secondary">
                            {isExpanded ? <ChevronUp className="h-4 w-4" /> : <ChevronDown className="h-4 w-4" />}
                          </div>
                        )}
                      </div>
                    </div>

                    {/* Step Details (Expandable logs) */}
                    {isExpanded && !isPending && (
                      <div className="border-t border-theme/60 bg-secondary/20 p-3.5 space-y-2">
                        <p className={`text-xs leading-relaxed whitespace-pre-wrap ${isFailed ? "text-red-500 font-medium" : "text-secondary"}`}>
                          {formatStepDetailsText(step)}
                        </p>
                      </div>
                    )}
                  </div>
                )
              })}
            </div>
          </>
        ) : (
          <div className="h-full flex flex-col items-center justify-center text-center p-6 space-y-3">
            <Layers className="h-8 w-8 text-muted opacity-40" />
            <div>
              <p className="text-sm font-semibold text-primary">No Active Inspector</p>
              <p className="text-xs text-secondary mt-1 max-w-[220px] mx-auto">
                Select an assistant message from the chat history to view its database queries and reasoning steps.
              </p>
            </div>
          </div>
        )}
      </div>
    </div>
  )
}
