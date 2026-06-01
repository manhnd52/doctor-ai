import type { Node, Edge } from "reactflow";
import type { GraphData } from "./types";
import {
    Background,
    Controls,
    ReactFlow,
    useNodesState,
    useEdgesState,
    ReactFlowProvider,
    useReactFlow,
} from "reactflow";

import "reactflow/dist/style.css";

import { useState, useEffect } from "react";

import { schema as rawSchema } from "../../assets/schema";
import { mapSchemaToGraphData } from "./types";
import SchemaNode from "./SchemaNode";
import CustomEdge from "./CustomEdge";
import ELK from "elkjs/lib/elk.bundled.js";

const defaultSchema = mapSchemaToGraphData(rawSchema);

export function buildGraph(graphData: GraphData) {
    const nodes: Node[] = graphData.nodes.map(
        (node: any) => ({
            id: node.id,

            position: {
                x: 0,
                y: 0,
            },

            data: {
                id: node.id,
                label: node.name,
                color: node.color,
                description: node.description,
                properties: node.properties,
                propertyCount: node.properties?.length || 0,
            },

            type: "schemaNode",
        })
    );

    // Group relationships by source and target
    const edgeMap = new Map<string, {
        source: string;
        target: string;
        labels: string[]; //multiple relationship types between two nodes
        relationships: any[];
    }>();

    graphData.edges.forEach((edge: any) => {
        const key = `${edge.source}->${edge.target}`;
        if (!edgeMap.has(key)) {
            edgeMap.set(key, {
                source: edge.source,
                target: edge.target,
                labels: [edge.name],
                relationships: [edge],
            });
        } else {
            const existing = edgeMap.get(key)!;
            if (!existing.labels.includes(edge.name)) {
                existing.labels.push(edge.name);
            }
            existing.relationships.push(edge);
        }
    });

    const edges: Edge[] = Array.from(edgeMap.values()).map((grouped) => {
        const combinedLabel = grouped.labels.join(" / ");

        return {
            id: `${grouped.source}-${grouped.target}`,
            source: grouped.source,
            target: grouped.target,
            label: combinedLabel,
            data: {
                id: combinedLabel,
                label: combinedLabel,
                properties: grouped.relationships.flatMap((r: any) => r.properties || []),
            },
            type: "customEdge",
            animated: true,
        };
    });

    return {
        nodes,
        edges,
    };
}

const elk = new ELK();

const elkOptions = {
    "elk.algorithm": "layered",
    "elk.direction": "RIGHT",
    "elk.edgeRouting": "ORTHOGONAL",
    "elk.spacing.nodeNode": "100",
    "elk.layered.spacing.nodeNodeBetweenLayers": "60",
    "elk.spacing.edgeNode": "60",
    "elk.layered.nodePlacement.strategy":
        "NETWORK_SIMPLEX",
    "elk.layered.crossingMinimization.strategy":
        "LAYER_SWEEP",
};

async function getLayoutedElements(nodes: Node[], edges: Edge[]) {
    const elkNodes = nodes.map((node) => ({
        id: node.id,
        width: 180,
        height: 120,
    }));

    const elkEdges = edges.map((edge) => ({
        id: edge.id,
        sources: [edge.source],
        targets: [edge.target],
    }));

    const layout = await elk.layout({
        id: "root",
        layoutOptions: elkOptions,
        children: elkNodes,
        edges: elkEdges,
    });

    return {
        nodes: nodes.map((node) => {
            const elkNode = layout.children?.find((n) => n.id === node.id);
            return {
                ...node,
                position: {
                    x: elkNode?.x ?? 0,
                    y: elkNode?.y ?? 0,
                },
            };
        }),
        edges,
    };
}

const nodeTypes = {
    schemaNode: SchemaNode,
};

const edgeTypes = {
    customEdge: CustomEdge,
};


interface SchemaGraphProps {
    schema?: GraphData;
}

function SchemaGraphInner({ schema = defaultSchema }: SchemaGraphProps) {
    const [nodes, setNodes, onNodesChange] = useNodesState([]);
    const [edges, setEdges, onEdgesChange] = useEdgesState([]);
    const { fitView } = useReactFlow();

    const [selected, setSelected] = useState<any>(null);

    useEffect(() => {
        const { nodes: initialNodes, edges: initialEdges } = buildGraph(schema);

        getLayoutedElements(initialNodes, initialEdges).then(
            ({ nodes: layoutedNodes, edges: layoutedEdges }) => {
                setNodes(layoutedNodes);
                setEdges(layoutedEdges);

                // Allow elements to render first then fit viewport
                window.requestAnimationFrame(() => {
                    fitView({ duration: 200, padding: 0.2 });
                });
            }
        );
    }, [schema, setNodes, setEdges, fitView]);

    return (
        <div
            style={{
                display: "flex",
                height: "100vh",
            }}
        >
            <div style={{ flex: 1 }}>
                <ReactFlow
                    nodes={nodes}
                    edges={edges}
                    onNodesChange={onNodesChange}
                    onEdgesChange={onEdgesChange}
                    nodeTypes={nodeTypes}
                    edgeTypes={edgeTypes}
                    onNodeClick={(_, node) =>
                        setSelected({
                            type: "node",
                            data: node.data,
                        })
                    }
                    onEdgeClick={(_, edge) =>
                        setSelected({
                            type: "relationship",
                            data: edge.data,
                        })
                    }
                    fitView
                >
                    <Background />
                    <Controls />
                </ReactFlow>
            </div>

            <PropertyPanel selected={selected} />
        </div>
    );
}

export default function SchemaGraph(props: SchemaGraphProps) {
    return (
        <ReactFlowProvider>
            <SchemaGraphInner {...props} />
        </ReactFlowProvider>
    );
}

type Props = {
    selected: any;
};

function PropertyPanel({
    selected,
}: Props) {
    if (!selected) {
        return (
            <div
                style={{
                    width: 350,
                    padding: 16,
                    borderLeft: "1px solid #ddd",
                }}
            >
                Select a node
            </div>
        );
    }

    const data = selected.data;

    return (
        <div
            style={{
                width: 350,
                padding: 16,
                borderLeft: "1px solid #ddd",
            }}
        >
            <h2>{data.label || data.id}</h2>

            {data.description && (
                <p>{data.description}</p>
            )}

            <h3>Properties</h3>

            <table>
                <tbody>
                    {data.properties?.map(
                        (prop: any) => (
                            <tr key={prop.name}>
                                <td>
                                    <b>{prop.name}</b>
                                </td>

                                <td>{prop.type}</td>
                            </tr>
                        )
                    )}
                </tbody>
            </table>
        </div>
    );
}