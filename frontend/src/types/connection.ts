export interface ConnectionRequest {
  uri: string
  username: string
  password: string
  database_name: string
}

export interface ConnectionStatus {
  success: boolean
  latency?: number
  version?: string
  node_count?: number
  relationship_count?: number
  error?: string
}