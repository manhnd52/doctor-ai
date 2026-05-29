interface LoginHeaderProps {
  logoSrc: string
  title?: string
  subtitle?: string
}

export default function LoginHeader({
  logoSrc,
  title = "Doctor AI",
  subtitle = "Intelligent Healthcare Assistant"
}: LoginHeaderProps) {
  return (
    <div className="flex flex-col items-center text-center">
      <div className="flex h-16 w-16 items-center justify-center rounded-2xl overflow-hidden mb-4 bg-primary">
        <img src={logoSrc} alt={`${title} Logo`} className="h-full w-full object-cover" />
      </div>
      <h1 className="text-2xl font-bold tracking-tight text-primary">
        {title}
      </h1>
      <p className="mt-1 text-sm text-secondary">
        {subtitle}
      </p>
    </div>
  )
}
