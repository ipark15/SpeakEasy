interface ScoreBadgeProps {
  score: number
  size?: "sm" | "md" | "lg"
}

export default function ScoreBadge({ score, size = "md" }: ScoreBadgeProps) {
  const color =
    score >= 80 ? "#16a34a" :
    score >= 60 ? "#d97706" :
    "#dc2626"

  const sizes = {
    sm: "text-2xl",
    md: "text-4xl",
    lg: "text-6xl",
  }

  return (
    <span className={`font-bold tabular-nums ${sizes[size]}`} style={{ color }}>
      {Math.round(score)}
    </span>
  )
}
