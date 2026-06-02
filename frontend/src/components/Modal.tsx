import { useEffect, useRef } from "react"
import { X } from "lucide-react"

interface ModalProps {
  isOpen: boolean
  onClose: () => void
  title?: React.ReactNode
  children: React.ReactNode
  size?: "sm" | "md" | "lg" | "xl" | "2xl" | "full"
  closeOnOverlayClick?: boolean
  showCloseButton?: boolean
  footer?: React.ReactNode
  className?: string
}

export default function Modal({
  isOpen,
  onClose,
  title,
  children,
  size = "md",
  closeOnOverlayClick = true,
  showCloseButton = true,
  footer,
  className = "",
}: ModalProps) {
  const modalRef = useRef<HTMLDivElement>(null)

  // Prevent background scrolling when modal is open
  useEffect(() => {
    if (isOpen) {
      document.body.style.overflow = "hidden"
    } else {
      document.body.style.overflow = ""
    }
    return () => {
      document.body.style.overflow = ""
    }
  }, [isOpen])

  // Handle Escape key press
  useEffect(() => {
    const handleKeyDown = (event: KeyboardEvent) => {
      if (event.key === "Escape" && isOpen) {
        onClose()
      }
    }
    window.addEventListener("keydown", handleKeyDown)
    return () => window.removeEventListener("keydown", handleKeyDown)
  }, [isOpen, onClose])

  if (!isOpen) return null

  // Map size strings to Tailwind max-width classes
  const sizeClasses = {
    sm: "max-w-[420px]",
    md: "max-w-[560px]",
    lg: "max-w-[760px]",
    xl: "max-w-[1020px]",
    "2xl": "max-w-[1280px]",
    full: "w-full h-full max-w-[calc(100vw-2rem)] max-h-[calc(100vh-2rem)] md:max-w-[calc(100vw-4rem)] md:max-h-[calc(100vh-4rem)]",
  }

  const handleOverlayClick = (e: React.MouseEvent) => {
    if (closeOnOverlayClick && modalRef.current && !modalRef.current.contains(e.target as Node)) {
      onClose()
    }
  }

  return (
    <div
      onClick={handleOverlayClick}
      className="fixed inset-0 z-50 flex items-center justify-center bg-neutral-950/60 backdrop-blur-md p-4 transition-all duration-300"
      aria-modal="true"
      role="dialog"
    >
      <div
        ref={modalRef}
        className={`relative flex w-full flex-col rounded-3xl border border-theme bg-panel shadow-[0_24px_64px_rgba(0,0,0,0.15)] outline-none animate-fadeIn ${
          size === "full" ? "h-full" : "max-h-[90vh]"
        } ${sizeClasses[size]} ${className}`}
      >
        {/* Modal Header */}
        {(title || showCloseButton) && (
          <div className="flex items-center justify-between border-b border-theme/60 px-6 py-4.5 sm:px-8">
            <div className="flex-1 min-w-0 pr-4">
              {typeof title === "string" ? (
                <h3 className="text-lg font-bold tracking-tight text-primary truncate">
                  {title}
                </h3>
              ) : (
                title
              )}
            </div>
            {showCloseButton && (
              <button
                onClick={onClose}
                className="inline-flex h-8 w-8 items-center justify-center rounded-xl border border-theme bg-secondary text-secondary hover:text-primary transition hover:bg-neutral-100 dark:hover:bg-neutral-800 active:scale-95 cursor-pointer"
                title="Close"
                aria-label="Close modal"
              >
                <X className="h-4 w-4" />
              </button>
            )}
          </div>
        )}

        {/* Modal Body */}
        <div className="flex-grow overflow-y-auto px-6 py-5 sm:px-8">
          {children}
        </div>

        {/* Modal Footer */}
        {footer && (
          <div className="border-t border-theme/60 bg-secondary/20 px-6 py-4 sm:px-8 rounded-b-3xl shrink-0">
            {footer}
          </div>
        )}
      </div>
    </div>
  )
}
