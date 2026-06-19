import { Outlet } from "react-router-dom"
import Header from "../components/Header"
import Sidebar from "../components/Sidebar"
import { useUIStore } from "../store/uiStore"

export default function MainLayout() {
  const { isSidebarOpen, setSidebarOpen } = useUIStore()

  return (
    <div className="flex h-screen w-screen overflow-hidden bg-primary font-sans antialiased text-primary">
      {/* Left Sidebar Backdrop for Mobile */}
      {isSidebarOpen && (
        <div
          className="fixed inset-0 z-30 bg-black/40 backdrop-blur-[2px] md:hidden cursor-pointer"
          onClick={() => setSidebarOpen(false)}
        />
      )}

      {/* Left Sidebar */}
      {isSidebarOpen && <Sidebar />}

      {/* Right Content Area (Header + Main Page Content) */}
      <div className="flex flex-col flex-1 min-w-0 h-full overflow-hidden relative">
        {/* Top Header */}
        <Header />

        {/* Main Workspace */}
        <main className="flex-grow h-full w-full relative overflow-hidden">
          <Outlet />
        </main>
      </div>
    </div>
  )
}