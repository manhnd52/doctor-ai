import { useState, useEffect } from "react"
import { useChatStore } from "../store/chatStore"
import { useUIStore } from "../store/uiStore"
import { chatService } from "../services/chatService"
import type { KnowledgeGraph } from "../types/ChatType"
import {
    Database,
    Check,
    Loader2,
    AlertCircle,
    RefreshCw,
    Server,
    Network,
    X
} from "lucide-react"

export default function KnowledgeGraphSelector() {
    const { createSession } = useChatStore()
    const { setGraphSelectorOpen } = useUIStore()
    const [graphs, setGraphs] = useState<KnowledgeGraph[]>([])
    const [loading, setLoading] = useState(true)
    const [error, setError] = useState<string | null>(null)
    const [selectedGraphId, setSelectedGraphId] = useState<number | null>(null)
    const [customTitle, setCustomTitle] = useState("")
    const [launching, setLaunching] = useState(false)

    const fetchGraphs = async () => {
        try {
            setLoading(true)
            setError(null)
            const data = await chatService.getKnowledgeGraphs()
            setGraphs(data)

            // Auto-select the first active graph if any
            const activeGraphs = data.filter(g => g.is_active)
            if (activeGraphs.length > 0) {
                setSelectedGraphId(activeGraphs[0].id)
            } else if (data.length > 0) {
                setSelectedGraphId(data[0].id)
            }
        } catch (err: any) {
            setError(
                err.response?.data?.detail ||
                err.message ||
                "Failed to load knowledge graphs."
            )
        } finally {
            setLoading(false)
        }
    }

    useEffect(() => {
        fetchGraphs()
    }, [])

    const handleLaunch = async () => {
        if (selectedGraphId === null) return
        try {
            setLaunching(true)
            const selectedGraph = graphs.find(g => g.id === selectedGraphId)
            const defaultTitle = selectedGraph
                ? `${selectedGraph.name}'s New Chat`
                : `Chat Session`

            const titleToUse = customTitle.trim() || defaultTitle
            await createSession(titleToUse, selectedGraphId)
            setGraphSelectorOpen(false)
        } catch (err) {
            console.error("Failed to launch session:", err)
        } finally {
            setLaunching(false)
        }
    }

    // Wrap loading, error, and empty states in the modal frame so it's always closable
    const renderModalContent = () => {
        if (loading) {
            return (
                <div className="flex-grow flex flex-col items-center justify-center py-12 select-none">
                    <Loader2 className="h-10 w-10 text-accent animate-spin mx-auto" />
                    <div className="space-y-1 text-center mt-4">
                        <h4 className="text-base font-semibold text-primary">Scanning Databases</h4>
                        <p className="text-xs text-secondary">Discovering available biomedical knowledge graphs...</p>
                    </div>
                </div>
            )
        }

        if (error) {
            return (
                <div className="flex-grow flex flex-col items-center justify-center py-8 select-none">
                    <div className="text-center space-y-4 max-w-[420px]">
                        <AlertCircle className="h-10 w-10 text-red-500 mx-auto" />
                        <div className="space-y-1">
                            <h4 className="font-semibold text-primary">Connection Failure</h4>
                            <p className="text-xs text-secondary leading-relaxed">{error}</p>
                        </div>
                        <button
                            onClick={fetchGraphs}
                            className="inline-flex items-center gap-2 rounded-xl bg-accent px-4 py-2 text-sm font-semibold text-black hover:brightness-110 active:scale-97 transition cursor-pointer"
                        >
                            <RefreshCw className="h-4 w-4" />
                            Retry Connection
                        </button>
                    </div>
                </div>
            )
        }

        if (graphs.length === 0) {
            return (
                <div className="flex-grow flex flex-col items-center justify-center py-8 select-none">
                    <div className="text-center space-y-4 max-w-[420px]">
                        <Database className="h-10 w-10 text-muted mx-auto" />
                        <div className="space-y-1">
                            <h4 className="font-semibold text-primary">No Graphs Configured</h4>
                            <p className="text-xs text-secondary leading-relaxed">
                                There are no active Neo4j database connections registered. Please log in as an administrator to establish a new connection.
                            </p>
                        </div>
                        <button
                            onClick={fetchGraphs}
                            className="inline-flex items-center gap-2 rounded-xl border border-theme bg-secondary px-4 py-2 text-sm font-medium hover:bg-primary/95 transition cursor-pointer"
                        >
                            <RefreshCw className="h-4 w-4" />
                            Check Again
                        </button>
                    </div>
                </div>
            )
        }

        return (
            <div className="flex-grow overflow-y-auto pr-1 space-y-6">
                {/* Card Grid */}
                <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                    {graphs.map((graph) => {
                        const isSelected = graph.id === selectedGraphId
                        const isGraphActive = graph.is_active

                        return (
                            <div
                                key={graph.id}
                                onClick={() => isGraphActive && setSelectedGraphId(graph.id)}
                                className={`relative flex flex-col justify-between rounded-2xl p-5 border transition-all duration-300 ${!isGraphActive
                                    ? "opacity-60 bg-secondary border-theme cursor-not-allowed"
                                    : isSelected
                                        ? "border-accent bg-accent-soft/5 shadow-[0_0_16px_rgba(16,163,127,0.12)] cursor-pointer"
                                        : "border-theme bg-panel hover:border-accent/40 hover:shadow-md cursor-pointer"
                                    }`}
                            >
                                {/* Selection indicator */}
                                {isSelected && (
                                    <div className="absolute top-4 right-4 flex h-6 w-6 items-center justify-center rounded-full bg-accent text-black">
                                        <Check className="h-4.5 w-4.5 stroke-[3]" />
                                    </div>
                                )}

                                <div className="space-y-3">
                                    {/* Title & Icon */}
                                    <div className="flex items-center gap-3">
                                        <div className={`p-2 rounded-xl ${isSelected ? "bg-accent-soft text-accent" : "bg-secondary text-secondary"
                                            }`}>
                                            <Network className="h-5 w-5" />
                                        </div>
                                        <div>
                                            <h4 className="font-semibold text-primary">{graph.name}</h4>
                                            {!isGraphActive && (
                                                <span className="inline-block text-[10px] uppercase font-bold text-red-500 tracking-wider">
                                                    Inactive
                                                </span>
                                            )}
                                        </div>
                                    </div>

                                    {/* Description */}
                                    <p className="text-xs text-secondary leading-relaxed line-clamp-3">
                                        {graph.description || "No description provided. This graph contains biomedical concepts, relationships, and supporting evidence."}
                                    </p>
                                </div>

                                {/* Connection details metadata */}
                                <div className="mt-5 pt-4 border-t border-theme/40 flex items-center justify-between text-[11px] text-muted font-mono">
                                    <div className="flex items-center gap-1.5">
                                        <Database className="h-3 w-3 text-secondary" />
                                        <span>{graph.database_name}</span>
                                    </div>
                                    <div className="flex items-center gap-1.5 max-w-[150px] truncate">
                                        <Server className="h-3 w-3 text-secondary" />
                                        <span className="truncate" title={graph.uri}>{graph.uri}</span>
                                    </div>
                                </div>
                            </div>
                        )
                    })}
                </div>

                {/* Actions panel */}
                <div className="rounded-2xl border border-theme bg-panel p-6 shadow-sm space-y-5">
                    <div className="flex flex-col gap-2">
                        <label htmlFor="session-title" className="text-xs font-semibold text-secondary uppercase tracking-wider">
                            Chat Title
                        </label>
                        <input
                            id="session-title"
                            type="text"
                            placeholder={
                                selectedGraphId !== null
                                    ? `${graphs.find(g => g.id === selectedGraphId)?.name}'s New Chat`
                                    : "New Chat"
                            }
                            value={customTitle}
                            onChange={(e) => setCustomTitle(e.target.value)}
                            className="w-full rounded-xl border border-theme bg-primary px-4 py-3 text-sm text-primary placeholder-secondary/40 outline-none transition focus:border-accent"
                            maxLength={50}
                        />
                    </div>

                    <button
                        onClick={handleLaunch}
                        disabled={selectedGraphId === null || launching}
                        className="w-full bg-accent hover:brightness-110 text-black disabled:opacity-50 disabled:cursor-not-allowed py-3.5 px-6 rounded-xl font-bold transition-all duration-300 flex items-center justify-center gap-2 select-none active:scale-[0.99] cursor-pointer shadow-md shadow-accent/5"
                    >
                        {launching ? (
                            <>
                                <Loader2 className="h-5 w-5 animate-spin" />
                                <span>Starting...</span>
                            </>
                        ) : (
                            <>
                                <span>Chat</span>
                            </>
                        )}
                    </button>
                </div>
            </div>
        )
    }

    return (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/60 p-4 sm:p-6 select-none overflow-y-auto">
            {/* Modal Box */}
            <div className="relative w-full max-w-[760px] rounded-3xl border border-theme bg-panel p-6 sm:p-8 shadow-[0_20px_50px_rgba(0,0,0,0.3)] flex flex-col max-h-[90vh] overflow-hidden animate-fadeIn">

                {/* Modal Header */}
                <div className="flex items-center justify-between pb-4 border-b border-theme mb-6">
                    <div>
                        <h3 className="text-xl font-bold text-primary">Select Knowledge Graph</h3>
                        <p className="text-xs text-secondary mt-0.5">
                            Choose a specialized biomedical knowledge graph connection to initialize your chat.
                        </p>
                    </div>
                    {/* Close (X) button */}
                    <button
                        onClick={() => setGraphSelectorOpen(false)}
                        className="p-2 rounded-xl border border-theme hover:bg-secondary text-secondary hover:text-primary transition cursor-pointer"
                        title="Close"
                    >
                        <X className="h-4.5 w-4.5" />
                    </button>
                </div>

                {/* Modal Content */}
                {renderModalContent()}

            </div>
        </div>
    )
}
