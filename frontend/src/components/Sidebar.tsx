import { useState } from "react"
import { Plus, Search, MessageSquare, Trash2, Edit3, Check, X, Bot } from "lucide-react"
import { useChatStore } from "../store/chatStore"
import { useUIStore } from "../store/uiStore"
import type { ChatSession } from "../types/ChatType"

export default function Sidebar() {
  const {
    sessions,
    activeSessionId,
    selectSession,
    deleteSession,
    updateSessionTitle,
  } = useChatStore()

  const { setGraphSelectorOpen, setSidebarOpen } = useUIStore()

  const [searchTerm, setSearchTerm] = useState("")
  const [editingId, setEditingId] = useState<number | null>(null)
  const [editTitle, setEditTitle] = useState("")

  const filteredSessions = sessions.filter((s) =>
    s.title.toLowerCase().includes(searchTerm.toLowerCase())
  )

  const handleStartEdit = (session: ChatSession, e: React.MouseEvent) => {
    e.stopPropagation()
    setEditingId(session.id)
    setEditTitle(session.title)
  }

  const handleSaveEdit = (id: number, e: React.MouseEvent) => {
    e.stopPropagation()
    if (editTitle.trim()) {
      updateSessionTitle(id, editTitle.trim())
    }
    setEditingId(null)
  }

  const handleCancelEdit = (e: React.MouseEvent) => {
    e.stopPropagation()
    setEditingId(null)
  }

  return (
    <div className="fixed inset-y-0 left-0 z-40 flex h-full w-[260px] flex-col border-r border-theme bg-panel text-primary select-none sm:w-[280px] md:relative md:inset-auto md:z-0 animate-slideInLeft md:animate-none shadow-2xl md:shadow-none">
      {/* Logo & Branding */}
      <div className="flex items-center gap-3 px-5 py-4 mb-2">
        <div className="flex h-8 w-8 shrink-0 items-center justify-center rounded-lg shadow-sm border bg-accent/10 border-accent/20 text-accent">
          <Bot className="h-4.5 w-4.5" />
        </div>
        <span className="font-semibold text-sm tracking-[0.18em] text-primary">
          Doctor.ai
        </span>
      </div>

      {/* New Chat Button */}
      <div className="px-4 pb-2">
        <button
          onClick={() => setGraphSelectorOpen(true)}
          className="flex w-full items-center justify-center gap-2 rounded-xl border border-theme bg-primary py-3 text-sm font-medium transition hover:bg-secondary active:scale-[0.98] cursor-pointer"
        >
          <Plus className="h-4 w-4" />
          New Chat
        </button>
      </div>

      {/* Search Input */}
      <div className="px-4 pb-2">
        <div className="relative flex items-center rounded-xl bg-secondary px-3 py-2 text-secondary focus-within:text-primary">
          <Search className="h-4 w-4 shrink-0" />
          <input
            type="text"
            placeholder="Search history..."
            value={searchTerm}
            onChange={(e) => setSearchTerm(e.target.value)}
            className="ml-2 w-full bg-transparent text-sm outline-none placeholder:text-muted"
          />
        </div>
      </div>

      {/* Chat History Section */}
      <div className="flex-1 overflow-y-auto px-2 py-2">
        <p className="px-3 py-1 text-xs font-semibold uppercase tracking-[0.2em] text-muted">
          Recently
        </p>

        <div className="mt-2 space-y-1">
          {filteredSessions.length > 0 ? (
            filteredSessions.map((session) => {
              const isActive = session.id === activeSessionId
              const isEditing = session.id === editingId

              return (
                <div
                  key={session.id}
                  onClick={() => {
                    if (!isEditing) {
                      selectSession(session.id)
                      if (window.innerWidth < 768) {
                        setSidebarOpen(false)
                      }
                    }
                  }}
                  className={`group relative flex items-center justify-between rounded-xl p-3 text-sm transition cursor-pointer ${isActive
                    ? "bg-secondary text-primary font-medium"
                    : "text-secondary hover:bg-secondary/60 hover:text-primary"
                    }`}
                >
                  <div className="flex flex-1 items-center min-w-0 mr-2">
                    <MessageSquare className="h-4 w-4 shrink-0 mr-3 text-muted group-hover:text-primary" />
                    {isEditing ? (
                      <input
                        type="text"
                        value={editTitle}
                        onChange={(e) => setEditTitle(e.target.value)}
                        className="w-full bg-primary px-2 py-0.5 rounded border border-accent outline-none text-sm"
                        autoFocus
                        onClick={(e) => e.stopPropagation()}
                      />
                    ) : (
                      <span className="truncate">{session.title}</span>
                    )}
                  </div>

                  {/* Actions (Delete/Rename) */}
                  <div className="flex items-center gap-1">
                    {isEditing ? (
                      <>
                        <button
                          onClick={(e) => handleSaveEdit(session.id, e)}
                          className="p-1 rounded hover:bg-secondary text-accent cursor-pointer"
                          title="Save"
                        >
                          <Check className="h-3.5 w-3.5" />
                        </button>
                        <button
                          onClick={handleCancelEdit}
                          className="p-1 rounded hover:bg-secondary text-red-500 cursor-pointer"
                          title="Cancel"
                        >
                          <X className="h-3.5 w-3.5" />
                        </button>
                      </>
                    ) : (
                      <div className="opacity-0 group-hover:opacity-100 flex items-center gap-0.5 transition">
                        <button
                          onClick={(e) => handleStartEdit(session, e)}
                          className="p-1 rounded hover:bg-primary text-secondary hover:text-primary cursor-pointer"
                          title="Rename"
                        >
                          <Edit3 className="h-3.5 w-3.5" />
                        </button>
                        <button
                          onClick={(e) => {
                            e.stopPropagation()
                            deleteSession(session.id)
                          }}
                          className="p-1 rounded hover:bg-primary text-secondary hover:text-red-500 cursor-pointer"
                          title="Delete"
                        >
                          <Trash2 className="h-3.5 w-3.5" />
                        </button>
                      </div>
                    )}
                  </div>
                </div>
              )
            })
          ) : (
            <p className="px-3 py-4 text-center text-xs text-muted">
              No sessions found
            </p>
          )}
        </div>
      </div>
    </div>
  )
}
