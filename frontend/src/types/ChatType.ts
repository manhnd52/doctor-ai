export interface ChatSession {
    id: number
    title: string
    created_at: string
    kg_id: number
}

export interface KnowledgeGraph {
    id: number
    name: string
    description?: string
    uri: string
    database_name: string
    is_active: boolean
    created_at: string
    schema: Object
}
