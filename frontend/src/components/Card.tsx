interface CardProps {
  children: React.ReactNode
  className?: string
}

export default function Card({ children, className = "" }: CardProps) {
  return (
    <div className={`rounded-[24px] p-6 sp-card ${className}`}>
      {children}
    </div>
  )
}
