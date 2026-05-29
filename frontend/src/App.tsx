import { useEffect } from 'react'
import './App.css'
import AppRoutes from "@/routes/index.tsx";
import { useUserStore } from "./store/userStore";

function App() {
  const fetchCurrentUser = useUserStore((state) => state.fetchCurrentUser)

  useEffect(() => {
    fetchCurrentUser()
  }, [fetchCurrentUser])

  return <AppRoutes />;
}

export default App