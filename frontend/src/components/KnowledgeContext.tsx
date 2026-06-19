import { useMemo } from "react"
import {
  X,
  Database,
  Link,
  Server,
} from "lucide-react"
import { useChatStore } from "../store/chatStore"
import { useUIStore } from "../store/uiStore"

interface DatabaseConnectMenuProps {
  isOpen: boolean
  onClose: () => void
}

export default function KnowledgeContext({ isOpen, onClose }: DatabaseConnectMenuProps) {
  const { activeSessionId, sessions } = useChatStore()
  const { setSchemaModalOpen } = useUIStore()

  const activeSession = useMemo(() => {
    return sessions.find((s) => s.id === activeSessionId)
  }, [sessions, activeSessionId])

  const activeGraph = activeSession?.knowledge_graph

  if (!isOpen || !activeGraph) return null

  return (
    <div className="fixed right-4 left-4 sm:left-auto sm:right-6 top-16 z-50 max-w-[calc(100vw-2rem)] sm:w-[380px] max-h-[82vh] flex flex-col rounded-2xl border border-theme bg-panel p-6 shadow-[0_20px_50px_rgba(0,0,0,0.15)] animate-fadeIn overflow-hidden">
      {/* Header */}
      <div className="mb-4 flex items-center justify-between pb-3 border-b border-theme shrink-0">
        <div className="flex items-center gap-2">
          <div className="h-7 w-7 rounded-lg bg-accent-soft text-accent flex items-center justify-center shrink-0">
            <Database className="h-4 w-4" />
          </div>
          <span className="text-xl font-bold text-primary font-sans truncate max-w-[240px]" title={activeGraph?.name || "Knowledge Graph"}>
            {activeGraph?.name || "Knowledge Graph"}
          </span>
        </div>
        <button
          onClick={onClose}
          aria-label="Close menu"
          className="inline-flex h-9 w-9 items-center justify-center rounded-xl border border-theme bg-panel text-secondary hover:text-primary transition hover:bg-secondary cursor-pointer"
        >
          <X className="h-4 w-4" />
        </button>
      </div>

      {/* Body Area */}
      <div className="flex-1 overflow-y-auto pr-1 space-y-4 min-h-0 text-sm font-sans">
        <div className="space-y-4">
          {/*Graph Description & Schema View Button*/}
          <div className="rounded-xl border border-theme bg-secondary p-4 space-y-4">
            <div className="flex items-center justify-between gap-4">
              <h3 className="font-semibold text-primary truncate text-xs uppercase tracking-wider text-secondary/80">Schema</h3>
              <button
                onClick={() => setSchemaModalOpen(true)}
                className="text-xs font-semibold text-accent hover:underline transition cursor-pointer"
              >
                View
              </button>
            </div>

            <div className="space-y-1.5">
              <h3 className="font-semibold text-primary truncate text-xs uppercase tracking-wider text-secondary/80">Description</h3>
              <p className="text-xs text-secondary leading-relaxed">
                {activeGraph.description || "No description provided. This graph connection serves biomedical information for RAG queries."}
              </p>
            </div>
          </div>

          {/* Connection Info */}
          <div className="space-y-2">
            <h4 className="text-[10px] font-bold uppercase tracking-wider text-secondary/80">Connection Details</h4>
            <div className="space-y-2">
              <div className="flex justify-between items-center text-sm py-2.5">
                <div className="flex items-center gap-2 text-primary">
                  <Link className="h-3.5 w-3.5" />
                  <span>Host / URI</span>
                </div>
                <span className="font-mono text-secondary truncate max-w-[200px]" title={activeGraph.uri}>{activeGraph.uri}</span>
              </div>
              <div className="flex justify-between items-center text-sm py-2.5">
                <div className="flex items-center gap-2 text-primary">
                  <Server className="h-3.5 w-3.5" />
                  <span>Database</span>
                </div>
                <span className="font-mono text-secondary">{activeGraph.database_name}</span>
              </div>
            </div>
          </div>
        </div>
      </div>

      {/* Footer Close Button */}
      <div className="border-theme shrink-0 mt-4">
        <button
          onClick={onClose}
          className="w-full inline-flex items-center justify-center rounded-xl border border-theme bg-secondary py-2.5 text-sm font-semibold text-primary hover:bg-secondary/80 active:scale-98 transition cursor-pointer"
        >
          Close
        </button>
      </div>
    </div>
  )
}
