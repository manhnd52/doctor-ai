import axios from "axios"

export const api = axios.create({
  baseURL: import.meta.env.VITE_API_BASE_URL || "http://localhost:8000/api",
})

// Request interceptor to add Authorization token
api.interceptors.request.use(
  (config) => {
    const token = localStorage.getItem("chat_token")
    if (token && config.headers) {
      config.headers.Authorization = `Bearer ${token}`
    }
    return config
  },
  (error) => Promise.reject(error)
)

/**
 * Ensures the application is authenticated.
 * Tries to verify current token or log in with demo credentials.
 * If user does not exist, registers them first.
 */
export async function ensureAuthenticated(): Promise<string> {
  const existingToken = localStorage.getItem("chat_token")

  if (existingToken) {
    try {
      // Test if current token is valid
      await api.get("/auth/me", {
        headers: { Authorization: `Bearer ${existingToken}` }
      })
      return existingToken
    } catch {
      localStorage.removeItem("chat_token")
      throw new Error("Session expired. Please login again.")
    }
  }

  throw new Error("No authentication token found. Please login.")
}
