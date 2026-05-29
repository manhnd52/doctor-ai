import { api } from "."
import type { ChatSession } from "../types/ChatType"
import type { Message } from "../components/MessageItem"

export const chatService = {
  async getSessions(): Promise<ChatSession[]> {
    const res = await api.get<ChatSession[]>("/chat/sessions")
    return res.data
  },

  async getMessages(sessionId: number): Promise<Message[]> {
    const res = await api.get<Message[]>(`/chat/sessions/${sessionId}/messages`)
    return res.data
  },

  async createSession(title: string): Promise<ChatSession> {
    const res = await api.post<ChatSession>("/chat/sessions", { title })
    return res.data
  },

  async deleteSession(sessionId: number): Promise<void> {
    await api.delete(`/chat/sessions/${sessionId}`)
  },

  async updateSessionTitle(sessionId: number, title: string): Promise<void> {
    await api.patch(`/chat/sessions/${sessionId}`, { title })
  },

  async sendMessageStream(
    sessionId: number,
    content: string,
    onEvent: (event: { event: string; data: any }) => void,
    signal?: AbortSignal
  ): Promise<void> {
    const token = localStorage.getItem("chat_token")
    const baseURL = api.defaults.baseURL || "http://localhost:8000/api"
    const response = await fetch(`${baseURL}/chat/sessions/${sessionId}/messages`, {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
        ...(token ? { Authorization: `Bearer ${token}` } : {}),
      },
      body: JSON.stringify({ content }),
      signal,
    })

    if (!response.ok) {
      const errorText = await response.text()
      throw new Error(errorText || `HTTP error! status: ${response.status}`)
    }

    const reader = response.body?.getReader()
    if (reader) {
      const decoder = new TextDecoder()
      let done = false
      let buffer = ""
      while (!done) {
        const { value, done: doneReading } = await reader.read()
        done = doneReading
        if (value) {
          const chunkStr = decoder.decode(value, { stream: !done })
          buffer += chunkStr
          const parts = buffer.split(/\r?\n\r?\n/)
          buffer = parts.pop() || ""

          for (const part of parts) {
            if (!part.trim()) continue

            let eventType = "message"
            let dataText = ""

            const lines = part.split(/\r?\n/)
            for (const line of lines) {
              const trimmed = line.trim()
              if (trimmed.startsWith("event:")) {
                eventType = trimmed.replace("event:", "").trim()
              } else if (trimmed.startsWith("data:")) {
                dataText = trimmed.replace("data:", "").trim()
              }
            }

            if (dataText) {
              try {
                const parsedData = JSON.parse(dataText)
                onEvent({ event: eventType, data: parsedData })
              } catch (e) {
                onEvent({ event: eventType, data: dataText })
              }
            }
          }
        }
      }

      if (buffer.trim()) {
        let eventType = "message"
        let dataText = ""
        const lines = buffer.split(/\r?\n/)
        for (const line of lines) {
          const trimmed = line.trim()
          if (trimmed.startsWith("event:")) {
            eventType = trimmed.replace("event:", "").trim()
          } else if (trimmed.startsWith("data:")) {
            dataText = trimmed.replace("data:", "").trim()
          }
        }
        if (dataText) {
          try {
            const parsedData = JSON.parse(dataText)
            onEvent({ event: eventType, data: parsedData })
          } catch (e) {
            console.log("Parse error:", e, dataText)
            onEvent({ event: eventType, data: dataText })
          }
        }
      }
    }
  }
}
