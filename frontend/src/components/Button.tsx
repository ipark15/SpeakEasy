interface ButtonProps {
  children: React.ReactNode
  onClick?: () => void
  disabled?: boolean
  variant?: "primary" | "outline"
  className?: string
  type?: "button" | "submit"
}

export default function Button({
  children,
  onClick,
  disabled = false,
  variant = "primary",
  className = "",
  type = "button",
}: ButtonProps) {
  const base = "rounded-[16px] px-6 py-3 font-medium transition-all duration-150 cursor-pointer"
  const variants = {
    primary: "bg-[#4338ca] text-white hover:bg-[#3730a3] disabled:opacity-50 disabled:cursor-not-allowed",
    outline: "border border-[#4338ca] text-[#4338ca] hover:bg-[#4338ca] hover:text-white disabled:opacity-50 disabled:cursor-not-allowed",
  }

  return (
    <button
      type={type}
      onClick={onClick}
      disabled={disabled}
      className={`${base} ${variants[variant]} ${className}`}
    >
      {children}
    </button>
  )
}
