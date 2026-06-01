import { Handle, Position } from "reactflow";

interface SchemaNodeProps {
    data: {
        label: string;
        color?: string;
        propertyCount?: number;
    };
}

export default function SchemaNode({ data }: SchemaNodeProps) {
    const propertyCount = data.propertyCount ?? 0;

    return (
        <div className="group relative cursor-pointer transition-all duration-250 ease-[cubic-bezier(0.175,0.885,0.32,1.275)] hover:scale-108 hover:z-10">
            {/* Top Handle (Target) */}
            <Handle
                type="target"
                position={Position.Top}
                className="!w-2 !h-2 !bg-[rgba(0,0,0,0.3)] !border-2 !border-white transition-all duration-200 group-hover:!bg-white group-hover:!scale-120"
            />

            {/* Circular Node Body */}
            <div
                style={{
                    background: data.color || "#68BDF6",
                }}
                className="w-[100px] h-[100px] rounded-full text-white flex flex-col items-center justify-center shadow-[0_4px_10px_rgba(0,0,0,0.15)] group-hover:shadow-[0_8px_20px_rgba(0,0,0,0.25)] border-3 border-white p-2 box-border transition-all duration-250"
            >
                <div
                    style={{
                        display: "-webkit-box",
                        WebkitLineClamp: 3,
                        WebkitBoxOrient: "vertical",
                    }}
                    className="font-bold text-[13px] text-center break-words leading-tight max-h-[3.6em] overflow-hidden text-ellipsis"
                    title={data.label}
                >
                    {data.label}
                </div>
            </div>

            {/* Property Count Badge (Neo4j Bloom style bubble indicator) */}
            {propertyCount > 0 && (
                <div
                    className="absolute -top-0.5 -right-0.5 bg-[#333333] text-white rounded-full w-[22px] h-[22px] flex items-center justify-center text-[10px] font-bold border-2 border-white shadow-[0_2px_6px_rgba(0,0,0,0.2)] z-5"
                    title={`${propertyCount} properties`}
                >
                    {propertyCount}
                </div>
            )}

            {/* Bottom Handle (Source) */}
            <Handle
                type="source"
                position={Position.Bottom}
                className="!w-2 !h-2 !bg-[rgba(0,0,0,0.3)] !border-2 !border-white transition-all duration-200 group-hover:!bg-white group-hover:!scale-120"
            />
        </div>
    );
}