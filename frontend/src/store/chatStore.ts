import { create } from "zustand"
import { chatService } from "../services/chatService"
import type { ChatSession } from "../types/ChatType"
import type { Message, PipelineRun } from "../components/MessageItem"

export function getStepDisplayName(stepName: string): string {
  const mapping: Record<string, string> = {
    entity_extraction: "Entity Extraction",
    triple_extraction: "Triple Extraction",
    triple_remediation: "Triple Remediation",
    entity_linking: "Entity Linking",
    cypher_generation: "Cypher Generation",
    cypher_validation: "Cypher Validation",
    cypher_correction: "Cypher Correction",
    query_execution: "Neo4j Query Execution",
    evaluation: "Evaluation",
    answer_generation: "Answer Synthesis",
  }
  return mapping[stepName] || stepName.replace(/_/g, " ").replace(/\b\w/g, c => c.toUpperCase())
}

interface SessionState {
  messages: Message[]
  sending_message: boolean
  streamingMessage: string | null
  streamingQuestionType: "PIPELINE" | "LLM" | null
  streamingError: string | null
  streamingRunningStep: string | null
  streamingPipelineRun: PipelineRun | null
}

interface ChatState {
  sessions: ChatSession[]
  activeSessionId: number | null
  sessionStates: Record<number, SessionState>
  messages: Message[]
  loading: boolean
  sending_message: boolean
  streamingMessage: string | null
  streamingQuestionType: "PIPELINE" | "LLM" | null
  streamingError: string | null
  streamingRunningStep: string | null
  streamingPipelineRun: PipelineRun | null
  abortControllers: Record<number, AbortController>

  loadSessions: () => Promise<void>
  selectSession: (id: number) => Promise<void>
  createSession: (title: string, knowledgeGraphId: number) => Promise<ChatSession | null>
  deleteSession: (id: number) => Promise<void>
  updateSessionTitle: (id: number, title: string) => Promise<void>
  sendMessage: (content: string, customSessionId?: number) => Promise<void>
  stopSendMessage: (customSessionId?: number) => void
  clearActiveSession: () => void
  setStreamingMessage: (msg: string | null) => void
  setSessionState: (
    sessionId: number,
    updates: Partial<SessionState> | ((prev: SessionState) => Partial<SessionState>)
  ) => void
}

export const useChatStore = create<ChatState>((set, get) => ({
  sessions: [],
  activeSessionId: null,
  sessionStates: {},
  messages: [],
  loading: false,
  sending_message: false,
  streamingMessage: null,
  streamingQuestionType: null,
  streamingError: null,
  streamingRunningStep: null,
  streamingPipelineRun: null,
  abortControllers: {},

  setSessionState: (sessionId, updates) => {
    const currentStates = get().sessionStates
    const prevState = currentStates[sessionId] || {
      messages: [],
      sending_message: false,
      streamingMessage: null,
      streamingQuestionType: null,
      streamingError: null,
      streamingRunningStep: null,
      streamingPipelineRun: null,
    }

    const resolvedUpdates = typeof updates === "function" ? updates(prevState) : updates
    const newState = { ...prevState, ...resolvedUpdates }

    const nextSessionStates = {
      ...currentStates,
      [sessionId]: newState,
    }

    const storeUpdates: Partial<ChatState> = {
      sessionStates: nextSessionStates,
    }

    // If active session is the one being updated, update it in the main state too (micro state)
    if (get().activeSessionId === sessionId) {
      Object.assign(storeUpdates, resolvedUpdates)
    }

    set(storeUpdates)
  },

  setStreamingMessage: (msg) => {
    const activeId = get().activeSessionId
    if (activeId !== null) {
      get().setSessionState(activeId, { streamingMessage: msg })
    } else {
      set({ streamingMessage: msg })
    }
  },

  clearActiveSession: () => set({
    activeSessionId: null,
    messages: [],
    sending_message: false,
    streamingMessage: null,
    streamingQuestionType: null,
    streamingError: null,
    streamingRunningStep: null,
    streamingPipelineRun: null,
  }),

  loadSessions: async () => {
    try {
      set({ loading: true })
      const data = await chatService.getSessions()
      set({ sessions: data })
      // Auto-select the first session if available
      if (data.length > 0 && get().activeSessionId === null) {
        get().selectSession(data[0].id)
      }
    } catch (err) {
      console.error("Failed to load sessions:", err)
    } finally {
      set({ loading: false })
    }
  },

  selectSession: async (id) => {
    const currentStates = get().sessionStates
    const sessionState = currentStates[id] || {
      messages: [],
      sending_message: false,
      streamingMessage: null,
      streamingQuestionType: null,
      streamingError: null,
      streamingRunningStep: null,
      streamingPipelineRun: null,
    }

    set({
      activeSessionId: id,
      messages: sessionState.messages,
      sending_message: sessionState.sending_message,
      streamingMessage: sessionState.streamingMessage,
      streamingQuestionType: sessionState.streamingQuestionType,
      streamingError: sessionState.streamingError,
      streamingRunningStep: sessionState.streamingRunningStep,
      streamingPipelineRun: sessionState.streamingPipelineRun,
      sessionStates: {
        ...currentStates,
        [id]: sessionState,
      }
    })

    try {
      const data = await chatService.getMessages(id)
      get().setSessionState(id, { messages: data })
    } catch (err) {
      console.error("Failed to load messages:", err)
    }
  },

  createSession: async (title: string = "", knowledgeGraphId: number) => {
    try {
      const sessionTitle = title ? title : `Chat ${get().sessions.length + 1}`
      const newSession = await chatService.createSession(sessionTitle, knowledgeGraphId)
      set((state) => ({ sessions: [newSession, ...state.sessions] }))
      get().selectSession(newSession.id)
      return newSession
    } catch (err) {
      console.error("Failed to create session:", err)
      return null
    }
  },

  deleteSession: async (id) => {
    try {
      await chatService.deleteSession(id)
      set((state) => {
        const nextSessionStates = { ...state.sessionStates }
        delete nextSessionStates[id]
        const isDeletingActive = state.activeSessionId === id
        return {
          sessions: state.sessions.filter((s) => s.id !== id),
          sessionStates: nextSessionStates,
          ...(isDeletingActive ? {
            activeSessionId: null,
            messages: [],
            sending_message: false,
            streamingMessage: null,
            streamingQuestionType: null,
            streamingError: null,
            streamingRunningStep: null,
            streamingPipelineRun: null,
          } : {})
        }
      })
    } catch (err) {
      console.error("Failed to delete session:", err)
    }
  },

  updateSessionTitle: async (id, title) => {
    try {
      await chatService.updateSessionTitle(id, title)
      set((state) => ({
        sessions: state.sessions.map((s) => (s.id === id ? { ...s, title } : s)),
      }))
    } catch (err) {
      console.error("Failed to update session title:", err)
    }
  },

  sendMessage: async (content, customSessionId) => {
    const sessionId = customSessionId || get().activeSessionId
    if (!sessionId) return

    // Abort existing stream if any
    if (get().abortControllers[sessionId]) {
      get().abortControllers[sessionId].abort()
    }

    const controller = new AbortController()
    set((state) => ({
      abortControllers: {
        ...state.abortControllers,
        [sessionId]: controller
      }
    }))

    let isAborted = false
    controller.signal.addEventListener("abort", () => {
      isAborted = true
    })

    const initialPipelineRun: PipelineRun = {
      id: -1,
      question: content,
      query: "",
      status: "running",
      trace_data: {
        steps: [],
        question_type: undefined,
      }
    }

    get().setSessionState(sessionId, {
      sending_message: true,
      streamingMessage: "Thinking...",
      streamingQuestionType: null,
      streamingError: null,
      streamingRunningStep: null,
      streamingPipelineRun: initialPipelineRun
    })

    const tempUserMsg: Message = {
      id: Date.now(),
      role: "user",
      content,
      created_at: new Date().toISOString(),
    }
    const currentMessages = get().sessionStates[sessionId]?.messages || []
    get().setSessionState(sessionId, { messages: [...currentMessages, tempUserMsg] })

    // Setup asynchronous event playback queue
    const eventQueue: { event: string; data: any }[] = []
    let queueProcessing = false

    const processQueue = async () => {
      if (queueProcessing) return
      queueProcessing = true

      while (eventQueue.length > 0 && !isAborted) {
        const nextEvent = eventQueue.shift()
        if (!nextEvent) break

        const { event: eventType, data } = nextEvent
        console.log("Processing queued event:", eventType, data)

        if (eventType === "CLASSIFY") {
          const qType = data.question_type
          get().setSessionState(sessionId, (prev) => {
            const nextRun = prev.streamingPipelineRun ? {
              ...prev.streamingPipelineRun,
              trace_data: {
                ...prev.streamingPipelineRun.trace_data,
                question_type: qType
              }
            } : null
            return {
              streamingQuestionType: qType,
              streamingMessage: qType === "LLM"
                ? "General conversation detected..."
                : "Running analysis pipeline...",
              streamingPipelineRun: nextRun
            }
          })
          console.log("Question type set to: ", qType)
        } else if (eventType === "RUNNING") {
          const stepName = data.running_step
          get().setSessionState(sessionId, (prev) => {
            const currentRun = prev.streamingPipelineRun
            let nextRun = null
            if (currentRun) {
              const updatedSteps = [...(currentRun.trace_data?.steps || [])]
              const existingIndex = updatedSteps.findLastIndex(s => s.name === stepName && s.status !== "completed")
              if (existingIndex !== -1) {
                updatedSteps[existingIndex] = {
                  ...updatedSteps[existingIndex],
                  status: "doing"
                }
              } else {
                updatedSteps.push({
                  name: stepName,
                  status: "doing"
                })
              }
              nextRun = {
                ...currentRun,
                trace_data: {
                  ...currentRun.trace_data,
                  steps: updatedSteps
                }
              }
            }
            return {
              streamingRunningStep: stepName,
              streamingMessage: `Starting step: ${getStepDisplayName(stepName)}...`,
              streamingPipelineRun: nextRun
            }
          })
        } else if (eventType === "STEP") {
          const stepName = data.step
          get().setSessionState(sessionId, (prev) => {
            const currentRun = prev.streamingPipelineRun
            let nextRun = null
            if (currentRun) {
              const updatedSteps = [...(currentRun.trace_data?.steps || [])]
              const existingIndex = updatedSteps.findLastIndex(s => s.name === stepName && s.status !== "completed")
              if (existingIndex !== -1) {
                updatedSteps[existingIndex] = {
                  ...updatedSteps[existingIndex],
                  status: "completed",
                  duration_ms: data.time,
                  details: typeof data.output === "object" ? JSON.stringify(data.output, null, 2) : String(data.output)
                }
              } else {
                updatedSteps.push({
                  name: stepName,
                  status: "completed",
                  duration_ms: data.time,
                  details: typeof data.output === "object" ? JSON.stringify(data.output, null, 2) : String(data.output)
                })
              }
              nextRun = {
                ...currentRun,
                trace_data: {
                  ...currentRun.trace_data,
                  steps: updatedSteps
                }
              }
            }
            return {
              streamingMessage: `Finished step: ${getStepDisplayName(stepName)} in ${data.time}ms.`,
              streamingPipelineRun: nextRun
            }
          })
        } else if (eventType === "ERROR") {
          get().setSessionState(sessionId, (prev) => {
            const currentRun = prev.streamingPipelineRun
            let nextRun = null
            if (currentRun) {
              nextRun = {
                ...currentRun,
                status: "failed"
              }
            }
            return {
              streamingError: data.error,
              streamingMessage: null,
              streamingPipelineRun: nextRun
            }
          })
          console.log("Error:", typeof data)
        } else if (eventType === "RESULT") {
          get().setSessionState(sessionId, (prev) => {
            const currentRun = prev.streamingPipelineRun
            let nextRun = null
            if (currentRun) {
              nextRun = {
                ...currentRun,
                status: "completed"
              }
            }
            return {
              streamingPipelineRun: nextRun
            }
          })
        }

        // Wait for 1 second if this is an intermediate event
        const isIntermediate = ["CLASSIFY", "RUNNING", "STEP"].includes(eventType)
        if (isIntermediate && !isAborted) {
          await new Promise((resolve) => setTimeout(resolve, 1000))
        }
      }
      queueProcessing = false
    }

    try {
      await chatService.sendMessageStream(sessionId, content, (event) => {
        eventQueue.push(event)
        processQueue()
      }, controller.signal)

      // Wait until the event queue is completely drained
      while ((queueProcessing || eventQueue.length > 0) && !isAborted) {
        await new Promise((resolve) => setTimeout(resolve, 100))
      }

      if (!isAborted) {
        const data = await chatService.getMessages(sessionId)
        get().setSessionState(sessionId, { messages: data })
      } else {
        console.log("Stream aborted by user during playback")
        const currentStreamingMsg = get().sessionStates[sessionId]?.streamingMessage || ""
        get().setSessionState(sessionId, {
          streamingMessage: currentStreamingMsg ? `${currentStreamingMsg} (Stopped)` : "Generation stopped by user."
        })
      }

    } catch (err: any) {
      if (err.name === "AbortError") {
        console.log("Stream aborted by user")
        const currentStreamingMsg = get().sessionStates[sessionId]?.streamingMessage || ""
        get().setSessionState(sessionId, {
          streamingMessage: currentStreamingMsg ? `${currentStreamingMsg} (Stopped)` : "Generation stopped by user."
        })
      } else {
        console.error("Error sending message:", err)
        get().setSessionState(sessionId, {
          streamingError: err.message || String(err),
          streamingMessage: null
        })
      }
    } finally {
      set((state) => {
        const nextControllers = { ...state.abortControllers }
        delete nextControllers[sessionId]
        return { abortControllers: nextControllers }
      })
      get().setSessionState(sessionId, { sending_message: false })
    }
  },

  stopSendMessage: (customSessionId) => {
    const sessionId = customSessionId || get().activeSessionId
    if (!sessionId) return
    const controller = get().abortControllers[sessionId]
    if (controller) {
      controller.abort()
    }
  }
}))
