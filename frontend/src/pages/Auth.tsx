import { useEffect } from "react"
import { useNavigate } from "react-router-dom"
import { useAuth } from "../hooks/useAuth"

export default function Auth() {
  const navigate = useNavigate()
  const { user, loading, signIn } = useAuth()

  useEffect(() => {
    if (loading) return
    if (user) {
      navigate("/dashboard", { replace: true })
    } else {
      signIn()
    }
  }, [user, loading])

  return (
    <div className="min-h-screen bg-[#edeaf8] flex items-center justify-center">
      <div className="text-center">
        <div className="flex items-end gap-0.5 justify-center mb-6">
          <span className="font-['Quicksand'] font-extrabold text-[32px] leading-[32px] text-[#4338ca] tracking-[-0.64px]">
            speakeas
          </span>
          <svg className="-ml-1" width="17" height="38" viewBox="0 0 22 27" fill="none">
            <path d="M11 3a3 3 0 0 1 3 3v7a3 3 0 0 1-6 0V6a3 3 0 0 1 3-3z" fill="#A8A9AD"/>
            <path d="M18 13v1a7 7 0 0 1-14 0v-1" stroke="#4338ca" strokeWidth="4" strokeLinecap="round"/>
            <line x1="11" y1="21" x2="11" y2="32" stroke="#4338ca" strokeWidth="4" strokeLinecap="round"/>
          </svg>
        </div>
        <p className="font-['Quicksand'] text-[14px] text-[#9896b0]">Redirecting to login…</p>
      </div>
    </div>
  )
}
