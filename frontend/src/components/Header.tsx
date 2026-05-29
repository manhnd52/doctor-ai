import { useState } from "react"
import { ChevronDown, Check, Menu, Layers, LogOut } from "lucide-react"
import { useNavigate } from "react-router-dom"
import DatabaseConnectMenu from "./DatabaseContextMenu"
import { useConnectionStore } from "../store/connectionStore"
import { useUIStore } from "../store/uiStore"
import { useUserStore } from "../store/userStore"
import chatbotLogo from "../assets/chatbot-ai.jpeg"

export default function Header() {
  const [isMenuOpen, setMenuOpen] = useState(false)
  const [isModelDropdownOpen, setModelDropdownOpen] = useState(false)
  const { status } = useConnectionStore()
  const isConnected = status?.success === true

  const {
    isSidebarOpen,
    toggleSidebar,
    isInspectorOpen,
    toggleInspector,
    selectedModel,
    setSelectedModel,
    hasPipelineRun,
  } = useUIStore()

  const { logout, user } = useUserStore()
  const navigate = useNavigate()

  return (
    <>
      <header className="flex h-14 w-full shrink-0 items-center justify-between border-b border-theme bg-panel px-4 text-primary shadow-[0_2px_12px_rgba(0,0,0,0.02)] select-none z-30">
        {/* Left Side: Menu button & Branding */}
        <div className="flex items-center gap-3">
          <button
            onClick={toggleSidebar}
            className="p-2 hover:bg-secondary rounded-lg transition active:scale-95 text-secondary hover:text-primary"
            title={isSidebarOpen ? "Hide Sidebar" : "Show Sidebar"}
          >
            <Menu className="h-5 w-5" />
          </button>

          <div className="flex items-center gap-2">
            <div className="flex h-8 w-8 items-center justify-center rounded-lg overflow-hidden shadow-sm">
              <img src={chatbotLogo} alt="Chatbot Logo" className="h-full w-full object-cover" />
            </div>
            <span className="font-semibold text-sm tracking-[0.18em] text-primary hidden sm:inline">
              DOCTOR AI CHATBOT
            </span>
          </div>
        </div>

        {/* Right Side: Model dropdown, DB status, and Inspector toggle */}
        <div className="flex items-center gap-3">
          {/* Database Connection Button */}
          <button
            type="button"
            onClick={() => setMenuOpen(true)}
            className="flex items-center gap-2 rounded-xl border border-theme bg-secondary px-3 py-1.5 text-xs font-semibold text-primary transition hover:bg-primary/95 active:scale-97"
          >
            <span
              className={`h-2 w-2 rounded-full ${isConnected ? "bg-emerald-500 shadow-[0_0_8px_rgba(16,185,129,0.5)]" : "bg-neutral-400"
                }`}
            />
            <span>{isConnected ? "Connected to DB" : "Connect KG"}</span>
          </button>

          {/* User profile & Logout */}
          {user && (
            <div className="flex items-center gap-2 border-l border-theme pl-3">
              <span className="text-xs font-semibold text-secondary hidden md:inline">
                {user.username}
              </span>
              <button
                type="button"
                onClick={() => {
                  logout()
                  navigate("/login")
                }}
                className="p-1.5 hover:bg-secondary rounded-lg transition text-secondary hover:text-red-500 cursor-pointer"
                title="Log Out"
              >
                <LogOut className="h-4.5 w-4.5" />
              </button>
            </div>
          )}

          {/* Toggle Inspector Button */}
          {hasPipelineRun && (
            <button
              onClick={toggleInspector}
              className={`p-1.5 rounded-xl border transition ${isInspectorOpen
                ? "border-accent bg-accent/10 text-accent"
                : "border-theme bg-secondary text-secondary hover:text-primary"
                }`}
              title="Toggle Inspector"
            >
              <Layers className="h-4.5 w-4.5" />
            </button>
          )}
        </div>
      </header>

      <DatabaseConnectMenu isOpen={isMenuOpen} onClose={() => setMenuOpen(false)} />
    </>
  )
}
