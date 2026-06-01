import { useState, useEffect, useMemo } from "react"
import {
  AlertTriangle,
  Layers,
  X,
  Database,
  Link,
  Loader2,
  Workflow,
  Server,
  User,
  Activity
} from "lucide-react"
import { useChatStore } from "../store/chatStore"
import { chatService } from "../services/chatService"
import type { KnowledgeGraph } from "../types/ChatType"

interface DatabaseConnectMenuProps {
  isOpen: boolean
  onClose: () => void
}

export default function KnowledgeContext({ isOpen, onClose }: DatabaseConnectMenuProps) {
  const { activeSessionId, sessions } = useChatStore()
  const [graphs, setGraphs] = useState<KnowledgeGraph[]>([])
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState<string | null>(null)

  useEffect(() => {
    if (isOpen) {
      const loadGraphs = async () => {
        try {
          setLoading(true)
          setError(null)
          const data = await chatService.getKnowledgeGraphs()
          setGraphs(data)
        } catch (err: any) {
          setError(
            err.response?.data?.detail ||
            err.message ||
            "Failed to load knowledge graphs"
          )
        } finally {
          setLoading(false)
        }
      }
      loadGraphs()
    }
  }, [isOpen])

  const activeSession = useMemo(() => {
    return sessions.find((s) => s.id === activeSessionId)
  }, [sessions, activeSessionId])

  const activeGraph = useMemo(() => {
    if (!activeSession) return null
    return graphs.find((g) => g.id === activeSession.kg_id)
  }, [graphs, activeSession])

  if (!isOpen) return null

  return (
    <div className="fixed right-6 top-16 z-50 w-[380px] max-h-[82vh] flex flex-col rounded-2xl border border-theme bg-panel p-6 shadow-[0_20px_50px_rgba(0,0,0,0.15)] animate-fadeIn overflow-hidden">
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
        {loading ? (
          <div className="py-12 flex flex-col items-center justify-center">
            <Loader2 className="h-8 w-8 text-accent animate-spin" />
            <p className="text-xs text-secondary mt-3">Loading graph configuration...</p>
          </div>
        ) : error ? (
          <div className="flex items-start gap-2.5 rounded-xl border border-red-200 bg-red-50 p-3.5 text-xs text-red-600">
            <AlertTriangle className="h-4 w-4 shrink-0 mt-0.5" />
            <span className="break-all">{error}</span>
          </div>
        ) : !activeSession ? (
          <div className="rounded-xl border border-theme bg-secondary p-5 text-center space-y-3">
            <Database className="h-10 w-10 text-muted mx-auto" />
            <div className="space-y-1">
              <h4 className="font-semibold text-primary">No Active Chat</h4>
              <p className="text-xs text-secondary leading-relaxed">
                Select an existing chat session from the sidebar or create a new chat to connect this workbench to a Knowledge Graph.
              </p>
            </div>
          </div>
        ) : !activeGraph ? (
          <div className="rounded-xl border border-red-500/20 bg-red-500/5 p-5 text-center space-y-3">
            <AlertTriangle className="h-10 w-10 text-red-500 mx-auto" />
            <div className="space-y-1">
              <h4 className="font-semibold text-red-500">Graph Disconnected</h4>
              <p className="text-xs text-secondary leading-relaxed">
                The Knowledge Graph connection for this session (ID: {activeSession.kg_id}) was not found or is inactive.
              </p>
            </div>
          </div>
        ) : (
          <div className="space-y-4">
            {/*Graph Description*/}
            <div className="rounded-xl border border-theme bg-secondary p-4 space-y-2">
              <div className="flex items-center gap-2.5">
                <h3 className="font-semibold text-primary truncate">Description</h3>
              </div>
              <p className="text-xs text-secondary leading-relaxed">
                {activeGraph.description || "No description provided. This graph connection serves biomedical information for RAG queries."}
              </p>
            </div>

            {/* Connection Info */}
            <div className="space-y-2">
              <h4 className="text-[10px] font-bold uppercase tracking-wider text-secondary/80">Connection Details</h4>
              <div className="space-y-2">
                <div className="flex justify-between items-center text-xs p-2.5 rounded-lg bg-secondary/50 border border-theme/40">
                  <div className="flex items-center gap-2 text-secondary">
                    <Link className="h-3.5 w-3.5" />
                    <span>Host / URI</span>
                  </div>
                  <span className="font-mono text-primary truncate max-w-[200px]" title={activeGraph.uri}>{activeGraph.uri}</span>
                </div>
                <div className="flex justify-between items-center text-xs p-2.5 rounded-lg bg-secondary/50 border border-theme/40">
                  <div className="flex items-center gap-2 text-secondary">
                    <Server className="h-3.5 w-3.5" />
                    <span>Database</span>
                  </div>
                  <span className="font-mono text-primary">{activeGraph.database_name}</span>
                </div>
                <div className="flex justify-between items-center text-xs p-2.5 rounded-lg bg-secondary/50 border border-theme/40">
                  <div className="flex items-center gap-2 text-secondary">
                    <User className="h-3.5 w-3.5" />
                    <span>User</span>
                  </div>
                  <span className="font-mono text-primary">{activeGraph.username}</span>
                </div>
                <div className="flex justify-between items-center text-xs p-2.5 rounded-lg bg-secondary/50 border border-theme/40">
                  <div className="flex items-center gap-2 text-secondary">
                    <Activity className="h-3.5 w-3.5" />
                    <span>Status</span>
                  </div>
                  <span className="inline-flex items-center gap-1.5 px-2 py-0.5 rounded-full text-[10px] font-semibold bg-emerald-500/10 text-emerald-500 border border-emerald-500/20">
                    <span className="h-1.5 w-1.5 rounded-full bg-emerald-500 animate-pulse" />
                    Connected
                  </span>
                </div>
              </div>
            </div>

            {/* Schema stats */}
            {activeGraph.schema && (
              <div className="space-y-3.5">
                <h4 className="text-[10px] font-bold uppercase tracking-wider text-secondary/80">Schema & Metadata</h4>

                {/* Stats cards */}
                <div className="grid grid-cols-2 gap-3.5">
                  <div className="rounded-xl border border-theme bg-secondary/40 p-3.5 flex items-start gap-3">
                    <Database className="h-4 w-4 text-accent mt-0.5 shrink-0" />
                    <div>
                      <p className="text-[10px] font-bold uppercase tracking-wider text-secondary/70">Entities</p>
                      <p className="text-lg font-bold mt-0.5">{activeGraph.schema?.labels?.length || 0}</p>
                    </div>
                  </div>
                  <div className="rounded-xl border border-theme bg-secondary/40 p-3.5 flex items-start gap-3">
                    <Workflow className="h-4 w-4 text-accent mt-0.5 shrink-0" />
                    <div>
                      <p className="text-[10px] font-bold uppercase tracking-wider text-secondary/70">Relations</p>
                      <p className="text-lg font-bold mt-0.5">{activeGraph.schema?.relationships?.length || 0}</p>
                    </div>
                  </div>
                </div>

                {/* Node labels list */}
                {activeGraph.schema.labels && activeGraph.schema.labels.length > 0 && (
                  <div className="space-y-2">
                    <label className="text-[10px] font-bold uppercase tracking-wider text-secondary/70">Entity Types</label>
                    <div className="flex flex-wrap gap-1.5 max-h-[120px] overflow-y-auto pr-1">
                      {activeGraph.schema.labels.map((lbl: any) => (
                        <span
                          key={lbl.id || lbl.name}
                          className="inline-flex items-center gap-1.5 px-2.5 py-1 rounded-full text-xs font-medium border border-theme bg-secondary/40 text-primary"
                        >
                          <span
                            className="h-2 w-2 rounded-full shrink-0"
                            style={{ backgroundColor: lbl.color || "#10a37f" }}
                          />
                          {lbl.name}
                        </span>
                      ))}
                    </div>
                  </div>
                )}
              </div>
            )}
          </div>
        )}
      </div>

      {/* Footer Close Button */}
      <div className="pt-4 border-t border-theme shrink-0 mt-4">
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
