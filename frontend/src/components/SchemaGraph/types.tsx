export interface PropertyDefinition {
    name: string;
    type: string;
}

export interface GraphNode {
    id: string;
    description?: string;
    name: string;
    color?: string;
    properties?: PropertyDefinition[];
}

export interface GraphEdge {
    id: string;
    source: string; // node id
    target: string; // node id
    name: string; // relationship type
    properties?: PropertyDefinition[];
}

export interface GraphData {
    nodes: GraphNode[];
    edges: GraphEdge[];
}

export function mapSchemaToGraphData(rawSchema: any): GraphData {
    const nodes: GraphNode[] = (rawSchema.labels || []).map((label: any) => ({
        id: label.id,
        description: label.description,
        name: label.name,
        color: label.color,
        properties: label.properties,
    }));

    const edges: GraphEdge[] = (rawSchema.relationships || []).map((rel: any, index: number) => ({
        id: rel.id || `${rel.source}-${rel.name}-${rel.target}-${index}`,
        source: rel.source,
        target: rel.target,
        name: rel.name,
        properties: rel.properties,
    }));

    return {
        nodes,
        edges,
    };
}
