import { useState, useEffect } from "react"
import MessageList from "../components/MessageList"
import KnowledgeGraphSelector from "../components/KnowledgeGraphSelector"
import type { Message, PipelineRun } from "../components/MessageItem"
import InputBox from "../components/InputBox"
import Inspector from "../components/Inspector"
import { ensureAuthenticated } from "../services"
import { useUIStore } from "../store/uiStore"
import { useChatStore } from "../store/chatStore"
import { AlertCircle, Loader2, Layers, Database } from "lucide-react"
import { useNavigate } from "react-router-dom"
import SchemaGraphModal from "../components/SchemaGraphModal"
import { convertSchemaToGraphData } from "../components/SchemaGraph/types"

export default function Chatbot() {
  const [authError, setAuthError] = useState<string | null>(null)
  const [selectedPipelineRun, setSelectedPipelineRun] = useState<PipelineRun | null>(null)
  const [pageLoading, setPageLoading] = useState(true)

  const {
    activeSessionId,
    messages,
    sending_message,
    streamingMessage,
    streamingQuestionType,
    streamingError,
    streamingPipelineRun,
    loadSessions,
    sendMessage,
    stopSendMessage,
    sessions,
  } = useChatStore()

  const {
    isInspectorOpen,
    setInspectorOpen,
    setHasPipelineRun,
    isGraphSelectorOpen,
    setGraphSelectorOpen,
    isSchemaModalOpen,
    setSchemaModalOpen,
  } = useUIStore()

  const activeSession = sessions.find((s) => s.id === activeSessionId)
  const navigate = useNavigate()

  useEffect(() => {
    setHasPipelineRun(!!selectedPipelineRun)
  }, [selectedPipelineRun, setHasPipelineRun])

  // Open selector modal by default if there are no chat sessions
  useEffect(() => {
    if (!pageLoading && sessions.length === 0) {
      setGraphSelectorOpen(true)
    }
  }, [pageLoading, sessions.length, setGraphSelectorOpen])

  // 1. Initial Authentication
  useEffect(() => {
    async function init() {
      try {
        setPageLoading(true)
        await ensureAuthenticated()
        await Promise.all([
          loadSessions(),
        ])
      } catch (err: any) {
        setAuthError(err.message || "Authentication failed. Please check if backend is running.")
      } finally {
        setPageLoading(false)
      }
    }
    init()
  }, [])

  // 2. Auto-select latest pipeline run when messages update
  useEffect(() => {
    const assistantMsgs = messages.filter((m: Message) => {
      if (m.role !== "assistant" || !m.pipeline_run) return false
      const run = m.pipeline_run
      const traceData = run.trace_data
      if (!traceData) return false
      const qType = traceData.question_type || (traceData.steps && traceData.steps.length > 0 ? "PIPELINE" : "LLM")
      return qType === "PIPELINE"
    })
    if (assistantMsgs.length > 0) {
      setSelectedPipelineRun(assistantMsgs[assistantMsgs.length - 1].pipeline_run!)
    } else {
      setSelectedPipelineRun(null)
    }
  }, [messages])

  // Render Loader
  if (pageLoading) {
    return (
      <div className="flex h-full w-full flex-col items-center justify-center bg-primary gap-4">
        <Loader2 className="h-10 w-10 text-accent animate-spin" />
        <p className="text-sm font-medium text-secondary">Loading...</p>
      </div>
    )
  }

  // Render Error
  if (authError) {
    return (
      <div className="flex h-full w-full flex-col items-center justify-center bg-primary p-6 text-center space-y-4">
        <AlertCircle className="h-12 w-12 text-red-500" />
        <h2 className="text-xl font-bold text-primary">Failed to Initialize Application</h2>
        <p className="text-sm text-secondary max-w-md">{authError}</p>
        <button
          onClick={() => navigate("/login")} // 
          className="rounded-xl bg-accent px-4 py-2.5 text-sm font-semibold text-black hover:brightness-110 transition cursor-pointer"
        >
          Go to Login
        </button>
      </div>
    )
  }

  return (
    <div className="flex h-full w-full overflow-hidden bg-primary font-sans">
      {/* Main Chat Area */}
      <div className="flex-1 flex flex-col h-full relative overflow-hidden bg-primary/30">
        {/* Message Viewport */}
        <div className="flex-grow flex flex-col min-h-0 overflow-y-auto">
          {activeSessionId ? (
            <MessageList
              messages={messages}
              onSelectPipelineRun={(run) => {
                setSelectedPipelineRun(run)
                setInspectorOpen(true)
              }}
              selectedPipelineRunId={selectedPipelineRun?.id || null}
            />
          ) : (
            <div className="flex-grow flex flex-col items-center justify-center p-8 select-none bg-primary/45 h-full">
              <div className="w-full max-w-[640px] text-center space-y-6 my-auto">
                <div className="inline-flex h-16 w-16 items-center justify-center rounded-2xl bg-accent-soft border border-accent/20 text-accent">
                  <Database className="h-8 w-8" />
                </div>
                <div className="space-y-2">
                  <h2 className="text-2xl font-bold text-primary">AI Research Workbench</h2>
                  <p className="text-sm text-secondary max-w-sm mx-auto">
                    Select a chat session from the sidebar or create a new chat to begin exploring.
                  </p>
                </div>
                <button
                  onClick={() => setGraphSelectorOpen(true)}
                  className="inline-flex items-center gap-2 rounded-xl bg-accent px-4 py-2.5 text-sm font-semibold text-black hover:brightness-110 active:scale-97 transition cursor-pointer"
                >
                  Create New Chat
                </button>
              </div>
            </div>
          )}

          {/* Streaming Indicator */}
          {sending_message && (streamingMessage || streamingError) && (
            <div className={`flex w-full py-6 justify-center border-b border-theme/40 transition-colors ${streamingError ? "bg-red-500/5 border-red-500/20" : "bg-secondary/40"
              }`}>
              <div className="flex w-full max-w-[720px] items-start gap-4 px-4 sm:gap-6">
                <div className={`flex h-8 w-8 shrink-0 items-center justify-center rounded-lg border ${streamingError
                  ? "bg-red-500/10 border-red-500/20 text-red-500"
                  : "bg-accent/10 border-accent/20 text-accent animate-pulse"
                  }`}>
                  {streamingError ? (
                    <AlertCircle className="h-4.5 w-4.5" />
                  ) : (
                    <Loader2 className="h-4.5 w-4.5 animate-spin" />
                  )}
                </div>
                <div className="flex-grow space-y-2">
                  <div className={`text-sm font-semibold tracking-wide uppercase ${streamingError ? "text-red-500" : "text-secondary"
                    }`}>
                    Assistant
                  </div>
                  <div className={`text-[15px] ${streamingError ? "text-red-500 font-medium" : "text-primary italic"
                    }`}>
                    {streamingError || streamingMessage}
                  </div>

                  {streamingQuestionType === "PIPELINE" && !streamingError && (
                    <div className="pt-2">
                      <button
                        onClick={() => setInspectorOpen(true)}
                        className="inline-flex items-center gap-1.5 rounded-lg bg-accent/10 hover:bg-accent/20 px-2.5 py-1 text-xs font-semibold text-accent border border-accent/20 transition cursor-pointer active:scale-95"
                      >
                        <Layers className="h-3 w-3" />
                        Pipeline Active
                      </button>
                    </div>
                  )}
                </div>
              </div>
            </div>
          )}
        </div>

        {/* Input Box */}
        {activeSessionId && (
          <InputBox
            onSendMessage={sendMessage}
            onStopSendMessage={stopSendMessage}
            isSending={sending_message}
            disabled={!activeSessionId}
            placeholder={
              !activeSessionId
                ? "Select or create a chat to begin..."
                : "Type a medical question or ask about Neo4j graph..."
            }
          />
        )}
      </div>

      {/* 3. Right Sidebar (Inspector) */}
      {isInspectorOpen && (selectedPipelineRun || (sending_message && streamingPipelineRun)) && (
        <Inspector
          pipelineRun={sending_message && streamingPipelineRun ? streamingPipelineRun : selectedPipelineRun}
          onClose={() => setInspectorOpen(false)}
        />
      )}

      {/* Selector Modal */}
      {isGraphSelectorOpen && <KnowledgeGraphSelector />}

      {/* Schema Graph Modal */}
      {isSchemaModalOpen && activeSession?.knowledge_graph?.schema && (
        <SchemaGraphModal
          isOpen={isSchemaModalOpen}
          onClose={() => setSchemaModalOpen(false)}
          schema={convertSchemaToGraphData(activeSession.knowledge_graph.schema)}
        />
      )}
    </div>
  )
}
