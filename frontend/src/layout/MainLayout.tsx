import { Outlet } from "react-router-dom"
import Header from "../components/Header"

export default function MainLayout() {
  return (
    <div className="flex h-screen w-screen flex-col overflow-hidden bg-primary font-sans antialiased text-primary">
      {/* Top Header */}
      <Header />

      {/* Main Workspace (Takes full remaining space) */}
      <div className="flex flex-1 min-h-0 overflow-hidden relative">
        <main className="flex-grow h-full w-full">
          <Outlet />
        </main>
      </div>
    </div>
  )
}