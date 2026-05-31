import { api } from "."

export interface UserMeResponse {
  username: string
  role?: string
}

export interface LoginResponse {
  access_token: string
}

export interface RegisterResponse {
  status: boolean
  access_token?: string
  errors: string[]
}

export const authService = {
  async login(username: string, password: string): Promise<LoginResponse> {
    const res = await api.post<LoginResponse>("/auth/login", { username, password })
    return res.data
  },

  async register(username: string, password: string): Promise<RegisterResponse> {
    const res = await api.post<RegisterResponse>("/auth/register", { username, password })
    return res.data
  },

  async getMe(token?: string): Promise<UserMeResponse> {
    const headers = token ? { Authorization: `Bearer ${token}` } : undefined
    const res = await api.get<UserMeResponse>("/auth/me", { headers })
    return res.data
  },

  validateLogin(username: string, password: string): string | null {
    if (!username.trim() || !password.trim()) {
      return "Please fill in all fields."
    }
    if (username.length < 3) {
      return "Username must be at least 3 characters long."
    }
    if (password.length < 6) {
      return "Password must be at least 6 characters long."
    }
    return null
  },

  validateRegister(username: string, password: string, confirmPassword: string): string | null {
    const loginError = this.validateLogin(username, password)
    if (loginError) return loginError
    if (password !== confirmPassword) {
      return "Passwords do not match."
    }
    return null
  }
}
