import React, { type ReactNode } from "react"

interface LoginInputProps extends React.InputHTMLAttributes<HTMLInputElement> {
  label: string
  icon: ReactNode
  rightElement?: ReactNode
}

export default function LoginInput({
  label,
  icon,
  rightElement,
  ...props
}: LoginInputProps) {
  return (
    <div className="space-y-1.5">
      <label className="text-[11px] font-semibold uppercase tracking-wider text-secondary">
        {label}
      </label>
      <div className="relative flex items-center">
        <div className="absolute left-3.5 text-secondary/60 flex items-center justify-center">
          {icon}
        </div>
        <input
          {...props}
          className={`w-full rounded-xl border border-theme bg-primary py-3 pl-10 text-sm text-primary placeholder-secondary/40 outline-none transition-all focus:border-accent focus:ring-1 focus:ring-accent/30 disabled:opacity-50 ${rightElement ? "pr-10" : "pr-4"
            }`}
        />
        {rightElement && (
          <div className="absolute right-3.5 flex items-center justify-center">
            {rightElement}
          </div>
        )}
      </div>
    </div>
  )
}
