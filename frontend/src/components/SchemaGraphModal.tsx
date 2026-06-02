import { useChatStore } from "@/store/chatStore"
import Modal from "./Modal"
import SchemaGraph from "./SchemaGraph/SchemaGraph"
import type { GraphData } from "./SchemaGraph/types"

interface SchemaGraphModalProps {
  isOpen: boolean
  onClose: () => void
  schema: GraphData
}

export default function SchemaGraphModal({
  isOpen,
  onClose,
  schema,
}: SchemaGraphModalProps) {
  const activeSessionId = useChatStore((state) => state.activeSessionId)
  const activeSession = useChatStore((state) => state.sessions.find((s) => s.id === activeSessionId))
  const knowledgeGraphName = activeSession?.knowledge_graph?.name

  return (
    <Modal
      isOpen={isOpen}
      onClose={onClose}
      title={knowledgeGraphName + "'s schema"}
      size="2xl"
      className="!max-h-[95vh]"
    >
      <div className="w-full h-[70vh] border border-theme/85 rounded-2xl overflow-hidden bg-secondary/15 flex flex-col">
        <SchemaGraph schema={schema} height="100%" />
      </div>
    </Modal>
  )
}
