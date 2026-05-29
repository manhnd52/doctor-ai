import { create } from "zustand"
import { authService } from "../services/authService"

interface UserState {
  user: { username: string } | null
  token: string | null
  loading: boolean
  error: string | null
  login: (username: string, password: string) => Promise<boolean>
  register: (username: string, password: string) => Promise<boolean>
  logout: () => void
  fetchCurrentUser: () => Promise<void>
  clearError: () => void
}

export const useUserStore = create<UserState>((set) => ({
  user: null,
  token: localStorage.getItem("chat_token"),
  loading: false,
  error: null,
  clearError: () => set({ error: null }),
  login: async (username, password) => {
    try {
      set({ loading: true, error: null })
      const data = await authService.login(username, password)
      const token = data.access_token
      localStorage.setItem("chat_token", token)
      set({ token, error: null })

      // Fetch current user details
      const user = await authService.getMe(token)
      set({ user })
      return true
    } catch (err: any) {
      const errMsg = err.response?.data?.detail || err.response?.data?.errors?.[0] || err.message || "Login failed"
      set({ error: errMsg })
      return false
    } finally {
      set({ loading: false })
    }
  },
  register: async (username, password) => {
    try {
      set({ loading: true, error: null })
      const data = await authService.register(username, password)
      if (data.status === false) {
        const errMsg = data.errors?.[0] || "Registration failed"
        set({ error: errMsg })
        return false
      }
      const token = data.access_token!
      localStorage.setItem("chat_token", token)
      set({ token, error: null })
      set({ user: { username } })
      return true
    } catch (err: any) {
      const errMsg = err.response?.data?.detail || err.response?.data?.errors?.[0] || err.message || "Registration failed"
      set({ error: errMsg })
      return false
    } finally {
      set({ loading: false })
    }
  },
  logout: () => {
    localStorage.removeItem("chat_token")
    set({ token: null, user: null })
  },
  fetchCurrentUser: async () => {
    const token = localStorage.getItem("chat_token")
    if (!token) {
      set({ token: null, user: null })
      return
    }
    try {
      set({ loading: true })
      const user = await authService.getMe()
      set({ user, token })
    } catch (err) {
      localStorage.removeItem("chat_token")
      set({ token: null, user: null })
    } finally {
      set({ loading: false })
    }
  }
}))

