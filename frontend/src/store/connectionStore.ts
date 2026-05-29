import { create } from "zustand"
import axios from "axios"

import { api } from "../services"

import type {
  ConnectionRequest,
  ConnectionStatus,
} from "../types/connection"

interface ConnectionStore {
  loading: boolean
  status: ConnectionStatus | null
  currentConnection: ConnectionRequest | null
  testConnection: (
    payload: ConnectionRequest
  ) => Promise<void>
  fetchCurrentConnection: () => Promise<void>
  disconnect: () => void
}

export const useConnectionStore =
  create<ConnectionStore>((set) => ({
    loading: false,
    status: null,
    currentConnection: null,
    disconnect: () => set({ status: null, currentConnection: null }),
    testConnection: async (
      payload: ConnectionRequest
    ) => {
      try {
        set({ loading: true })
        const res =
          await api.post<{
            status: boolean;
            error?: string;
            node_count?: number;
            relationship_count?: number
          }>(
            "/kg/connect",
            payload
          )

        if (res.data.status) {
          set({
            status: {
              success: true,
              node_count: res.data.node_count,
              relationship_count: res.data.relationship_count,
            },
            currentConnection: payload,
          })
        } else {
          set({
            status: {
              success: false,
              error: res.data.error || "Connection failed",
            },
            currentConnection: payload,
          })
        }
      } catch (err: unknown) {
        let errorMessage =
          "Connection failed"
        if (axios.isAxiosError(err)) {
          errorMessage =
            err.response?.data?.detail ||
            err.message
        }
        set({
          status: {
            success: false,
            error: errorMessage,
          },
          currentConnection: payload,
        })
      } finally {
        set({
          loading: false,
        })
      }
    },
    fetchCurrentConnection: async () => {
      try {
        set({ loading: true })
        const res = await api.get<{
          status: boolean
          message?: string
          current_connection?: {
            id: number
            user_id: number
            uri: string
            username: string
            password: string
            database_name: string
            node_count?: number
            relationship_count?: number
          }
        }>("/kg/current")

        if (res.data.status && res.data.current_connection) {
          const conn = res.data.current_connection
          set({
            status: {
              success: true,
              node_count: conn.node_count,
              relationship_count: conn.relationship_count,
            },
            currentConnection: {
              uri: conn.uri,
              username: conn.username,
              password: conn.password,
              database_name: conn.database_name,
            },
          })
        } else {
          set({ status: null, currentConnection: null })
        }
      } catch (err) {
        console.error("Failed to fetch current connection:", err)
        set({ status: null, currentConnection: null })
      } finally {
        set({ loading: false })
      }
    },
  }))