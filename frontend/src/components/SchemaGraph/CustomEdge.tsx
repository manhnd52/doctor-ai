import { getBezierPath, type EdgeProps, EdgeLabelRenderer } from "reactflow";

export default function CustomEdge({
    id,
    source,
    target,
    sourceX,
    sourceY,
    targetX,
    targetY,
    sourcePosition,
    targetPosition,
    style = {},
    markerEnd,
    label,
}: EdgeProps) {
    const isSelfLoop = source === target;

    let edgePath = "";
    let labelX = 0;
    let labelY = 0;

    if (isSelfLoop) {
        // Calculate dynamic spacing based on the label text length
        const labelText = typeof label === "string" ? label : "";
        const labelLength = labelText.length;

        const baseRadiusX = 65;
        const baseRadiusY = 45;

        // Scale out the loop at approximately 4.5px per character
        const dynamicOffset = labelLength * 4.5;

        const loopRadiusX = baseRadiusX + dynamicOffset;
        const loopRadiusY = baseRadiusY + dynamicOffset * 0.6;

        edgePath = `M ${sourceX} ${sourceY} C ${sourceX - loopRadiusX} ${sourceY + loopRadiusY}, ${targetX - loopRadiusX} ${targetY - loopRadiusY}, ${targetX} ${targetY}`;

        // Position the label at the outer midpoint of the curve loop
        labelX = sourceX - (loopRadiusX * 0.75);
        labelY = (sourceY + targetY) / 2;
    } else {
        // Use bezier path for standard edges to keep curves smooth and soft
        const [path, x, y] = getBezierPath({
            sourceX,
            sourceY,
            sourcePosition,
            targetX,
            targetY,
            targetPosition,
        });
        edgePath = path;
        labelX = x;
        labelY = y;
    }

    return (
        <>
            <path
                id={id}
                style={style}
                className="react-flow__edge-path stroke-gray-400 stroke-2 hover:stroke-indigo-500 transition-colors"
                d={edgePath}
                markerEnd={markerEnd}
            />

            {label && (
                <EdgeLabelRenderer>
                    <div
                        style={{
                            position: "absolute",
                            transform: `translate(-50%, -50%) translate(${labelX}px, ${labelY}px)`,
                            background: "#ffffff",
                            padding: "2px 6px",
                            borderRadius: 6,
                            border: "1px solid #e2e8f0",
                            fontSize: 10,
                            fontWeight: 600,
                            color: "#475569",
                            pointerEvents: "all",
                            userSelect: "none",
                        }}
                        className="nodrag nopan shadow-sm border border-slate-200"
                    >
                        {label}
                    </div>
                </EdgeLabelRenderer>
            )}
        </>
    );
}
