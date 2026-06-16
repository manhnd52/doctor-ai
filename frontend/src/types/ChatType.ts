export interface ChatSession {
    id: number
    title: string
    created_at: string
    knowledge_graph: KnowledgeGraph
}

export interface KnowledgeGraph {
    id: number
    name: string
    description?: string
    uri: string
    database_name: string
    username: string
    is_active: boolean
    created_at: string
    schema: any
}