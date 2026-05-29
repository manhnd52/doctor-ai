interface LoginTabsProps {
  isLoginTab: boolean
  onTabChange: (isLoginTab: boolean) => void
}

export default function LoginTabs({ isLoginTab, onTabChange }: LoginTabsProps) {
  return (
    <div className="mt-6 flex rounded-xl bg-secondary p-1 border border-theme">
      <button
        type="button"
        onClick={() => onTabChange(true)}
        className={`flex-1 rounded-lg py-2 text-xs font-semibold tracking-wide uppercase transition-all duration-200 cursor-pointer ${
          isLoginTab
            ? "bg-panel text-primary border border-theme/60 shadow-sm"
            : "text-secondary hover:text-primary"
        }`}
      >
        Sign In
      </button>
      <button
        type="button"
        onClick={() => onTabChange(false)}
        className={`flex-1 rounded-lg py-2 text-xs font-semibold tracking-wide uppercase transition-all duration-200 cursor-pointer ${
          !isLoginTab
            ? "bg-panel text-primary border border-theme/60 shadow-sm"
            : "text-secondary hover:text-primary"
        }`}
      >
        Sign Up
      </button>
    </div>
  )
}
