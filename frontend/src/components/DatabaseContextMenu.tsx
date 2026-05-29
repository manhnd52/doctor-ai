import { useMemo, useState, useEffect } from "react"
import type { ChangeEvent, FormEvent } from "react"
import {
  AlertTriangle,
  Eye,
  EyeOff,
  Layers,
  Rocket,
  X,
  Database,
  Key,
  User,
  Link,
  Loader2,
  Workflow,
} from "lucide-react"
import { useConnectionStore } from "../store/connectionStore"

const validateUri = (value: string) =>
  /^(bolt|neo4j):\/\/[\w\-._~:%@!$&'()*+,;=]+$/i.test(value)

interface DatabaseConnectMenuProps {
  isOpen: boolean
  onClose: () => void
}

export default function DatabaseConnectMenu({ isOpen, onClose }: DatabaseConnectMenuProps) {
  const [showPassword, setShowPassword] = useState(false)
  const [form, setForm] = useState({
    uri: "bolt://neo4j:7687",
    username: "neo4j",
    password: "",
    database_name: "neo4j",
  })
  const [validationError, setValidationError] = useState<string>("")

  const { status, loading, testConnection, disconnect, currentConnection } = useConnectionStore()
  const isConnected = status?.success === true
  const connectionError = status?.error ?? ""

  useEffect(() => {
    if (currentConnection) {
      setForm({
        uri: currentConnection.uri,
        username: currentConnection.username,
        password: currentConnection.password || "",
        database_name: currentConnection.database_name,
      })
    }
  }, [currentConnection])

  const uriError = useMemo(() => {
    if (!form.uri.trim()) return "URI is required"
    if (!validateUri(form.uri.trim()))
      return "URI must start with bolt:// or neo4j://"
    return ""
  }, [form.uri])

  const handleSubmit = async (event: FormEvent<HTMLFormElement>) => {
    event.preventDefault()
    setValidationError("")

    if (uriError) {
      setValidationError(uriError)
      return
    }

    await testConnection(form)
  }

  const handleFieldChange = (event: ChangeEvent<HTMLInputElement>) => {
    setForm({
      ...form,
      [event.target.name]: event.target.value,
    })

    if (status?.success === false) {
      disconnect()
    }

    if (validationError) {
      setValidationError("")
    }
  }

  const handleDisconnect = () => {
    disconnect()
    setForm((current) => ({ ...current, password: "" }))
  }

  if (!isOpen) {
    return null
  }

  return (
    <div className="fixed right-6 top-16 z-50 w-[360px] rounded-2xl border border-theme bg-panel p-6 shadow-[0_20px_50px_rgba(0,0,0,0.15)] animate-fadeIn">
      {/* Header */}
      <div className="mb-6 flex items-center justify-between">
        <div>
          <span className="text-[10px] font-bold uppercase tracking-[0.2em] text-accent">Neo4j Database</span>
          <h2 className="text-xl font-bold text-primary mt-0.5">Connect KG</h2>
        </div>
        <button
          onClick={onClose}
          aria-label="Close Neo4j menu"
          className="inline-flex h-9 w-9 items-center justify-center rounded-xl border border-theme bg-panel text-secondary hover:text-primary transition hover:bg-secondary cursor-pointer"
        >
          <X className="h-4 w-4" />
        </button>
      </div>

      {!isConnected ? (
        <form onSubmit={handleSubmit} className="space-y-4">
          {/* URI Input */}
          <div className="space-y-1.5">
            <label className="text-[10px] font-bold uppercase tracking-wider text-secondary/80">
              URI
            </label>
            <div className="relative flex items-center">
              <div className="absolute left-3.5 text-secondary/60 flex items-center justify-center">
                <Link className="h-4 w-4" />
              </div>
              <input
                name="uri"
                value={form.uri}
                onChange={handleFieldChange}
                placeholder="bolt://neo4j:7687"
                className="w-full rounded-xl border border-theme bg-primary py-3 pl-10 pr-4 text-sm text-primary placeholder-secondary/30 outline-none transition-all focus:border-accent focus:ring-1 focus:ring-accent/30"
              />
            </div>
          </div>

          {/* Database Input */}
          <div className="space-y-1.5">
            <label className="text-[10px] font-bold uppercase tracking-wider text-secondary/80">
              Database Name
            </label>
            <div className="relative flex items-center">
              <div className="absolute left-3.5 text-secondary/60 flex items-center justify-center">
                <Database className="h-4 w-4" />
              </div>
              <input
                name="database_name"
                value={form.database_name}
                onChange={handleFieldChange}
                placeholder="neo4j"
                className="w-full rounded-xl border border-theme bg-primary py-3 pl-10 pr-4 text-sm text-primary placeholder-secondary/30 outline-none transition-all focus:border-accent focus:ring-1 focus:ring-accent/30"
              />
            </div>
          </div>

          {/* Username Input */}
          <div className="space-y-1.5">
            <label className="text-[10px] font-bold uppercase tracking-wider text-secondary/80">
              Username
            </label>
            <div className="relative flex items-center">
              <div className="absolute left-3.5 text-secondary/60 flex items-center justify-center">
                <User className="h-4 w-4" />
              </div>
              <input
                name="username"
                value={form.username}
                onChange={handleFieldChange}
                placeholder="neo4j"
                className="w-full rounded-xl border border-theme bg-primary py-3 pl-10 pr-4 text-sm text-primary placeholder-secondary/30 outline-none transition-all focus:border-accent focus:ring-1 focus:ring-accent/30"
              />
            </div>
          </div>

          {/* Password Input */}
          <div className="space-y-1.5">
            <label className="text-[10px] font-bold uppercase tracking-wider text-secondary/80">
              Password
            </label>
            <div className="relative flex items-center">
              <div className="absolute left-3.5 text-secondary/60 flex items-center justify-center">
                <Key className="h-4 w-4" />
              </div>
              <input
                type={showPassword ? "text" : "password"}
                name="password"
                value={form.password}
                onChange={handleFieldChange}
                placeholder="••••••••"
                className="w-full rounded-xl border border-theme bg-primary py-3 pl-10 pr-10 text-sm text-primary placeholder-secondary/30 outline-none transition-all focus:border-accent focus:ring-1 focus:ring-accent/30"
              />
              <button
                type="button"
                onClick={() => setShowPassword((value) => !value)}
                className="absolute right-3.5 text-secondary/60 hover:text-primary transition cursor-pointer"
              >
                {showPassword ? <EyeOff className="h-4 w-4" /> : <Eye className="h-4 w-4" />}
              </button>
            </div>
          </div>

          {/* Actions */}
          <div className="flex items-center gap-3 pt-2">
            <button
              type="submit"
              disabled={loading}
              className="flex-1 inline-flex items-center justify-center gap-2 rounded-xl bg-accent py-3 text-sm font-semibold text-white shadow-sm hover:brightness-105 active:scale-98 transition disabled:opacity-50 cursor-pointer"
            >
              {loading ? (
                <Loader2 className="h-4 w-4 animate-spin" />
              ) : (
                <Rocket className="h-4 w-4" />
              )}
              <span>{loading ? "Connecting..." : "Connect"}</span>
            </button>
            <button
              type="button"
              onClick={onClose}
              className="inline-flex items-center justify-center rounded-xl border border-theme bg-secondary px-5 py-3 text-sm font-semibold text-primary hover:bg-secondary/80 active:scale-98 transition cursor-pointer"
            >
              Cancel
            </button>
          </div>

          {/* Error Message */}
          {(validationError || connectionError) && (
            <div className="flex items-start gap-2.5 rounded-xl border border-red-200 bg-red-50 p-3.5 text-xs text-red-600 animate-fadeIn">
              <AlertTriangle className="h-4 w-4 shrink-0 mt-0.5" />
              <span className="break-all">{validationError || connectionError}</span>
            </div>
          )}
        </form>
      ) : (
        <div className="space-y-4 text-primary">
          {/* Connection URI Card */}
          <div className="rounded-xl border border-theme bg-secondary p-4 flex items-start gap-3">
            <div className="h-8 w-8 rounded-lg bg-accent-soft text-accent flex items-center justify-center shrink-0">
              <Link className="h-4 w-4" />
            </div>
            <div className="min-w-0 flex-1">
              <p className="text-[10px] font-bold uppercase tracking-wider text-secondary/70">Connected to</p>
              <p className="font-semibold text-sm break-all mt-0.5">{form.uri}</p>
            </div>
          </div>

          {/* Graph Stats Grid */}
          <div className="grid grid-cols-2 gap-3">
            <div className="rounded-xl border border-theme bg-secondary p-4 flex items-start gap-3">
              <div className="h-8 w-8 rounded-lg bg-accent-soft text-accent flex items-center justify-center shrink-0">
                <Database className="h-4 w-4" />
              </div>
              <div>
                <p className="text-[10px] font-bold uppercase tracking-wider text-secondary/70">Nodes</p>
                <p className="text-xl font-bold mt-0.5">
                  {status?.node_count ?? "—"}
                </p>
              </div>
            </div>

            <div className="rounded-xl border border-theme bg-secondary p-4 flex items-start gap-3">
              <div className="h-8 w-8 rounded-lg bg-accent-soft text-accent flex items-center justify-center shrink-0">
                <Workflow className="h-4 w-4" />
              </div>
              <div>
                <p className="text-[10px] font-bold uppercase tracking-wider text-secondary/70">Rels</p>
                <p className="text-xl font-bold mt-0.5">
                  {status?.relationship_count ?? "—"}
                </p>
              </div>
            </div>
          </div>

          {/* Connected Actions */}
          <div className="space-y-2.5 pt-2">
            <button
              type="button"
              className="w-full inline-flex items-center justify-center gap-2 rounded-xl bg-accent py-3 text-sm font-semibold text-white shadow-sm hover:brightness-105 active:scale-98 transition cursor-pointer"
            >
              <Layers className="h-4 w-4" />
              View Schema
            </button>
            <button
              type="button"
              onClick={handleDisconnect}
              className="w-full inline-flex items-center justify-center rounded-xl border border-theme bg-secondary py-3 text-sm font-semibold text-red-600 hover:bg-red-50/50 hover:border-red-200 active:scale-98 transition cursor-pointer"
            >
              Disconnect
            </button>
          </div>
        </div>
      )}
    </div>
  )
}
