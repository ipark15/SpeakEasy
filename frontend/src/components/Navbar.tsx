import { useNavigate } from "react-router-dom"

interface NavbarProps {
  showActions?: boolean
}

export default function Navbar({ showActions = true }: NavbarProps) {
  const navigate = useNavigate()

  return (
    <nav
      style={{ background: "rgba(255,255,255,0.7)", borderBottom: "1px solid rgba(229,231,235,0.5)" }}
      className="sticky top-0 z-50 backdrop-blur-sm px-6 py-4 flex items-center justify-between"
    >
      <div className="flex items-center gap-2 cursor-pointer" onClick={() => navigate("/dashboard")}>
        <div className="w-8 h-8 bg-[#4338ca] rounded-lg flex items-center justify-center">
          <svg width="16" height="16" viewBox="0 0 24 24" fill="white">
            <path d="M12 2a3 3 0 0 1 3 3v6a3 3 0 0 1-6 0V5a3 3 0 0 1 3-3z"/>
            <path d="M19 10v1a7 7 0 0 1-14 0v-1"/>
            <line x1="12" y1="18" x2="12" y2="22"/>
            <line x1="8" y1="22" x2="16" y2="22"/>
          </svg>
        </div>
        <span className="font-['Outfit'] font-extrabold text-xl text-[#1e2939]">SpeakEasy</span>
      </div>

      {showActions && (
        <div className="flex items-center gap-3">
          <button
            onClick={() => navigate("/profile")}
            className="w-9 h-9 rounded-full bg-[#c7d2fe] flex items-center justify-center hover:bg-[#4338ca] hover:text-white transition-colors"
          >
            <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
              <path d="M20 21v-2a4 4 0 0 0-4-4H8a4 4 0 0 0-4 4v2"/>
              <circle cx="12" cy="7" r="4"/>
            </svg>
          </button>
          <button
            onClick={() => navigate("/settings")}
            className="w-9 h-9 rounded-full bg-[#e5e7eb] flex items-center justify-center hover:bg-[#4338ca] hover:text-white transition-colors"
          >
            <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
              <circle cx="12" cy="12" r="3"/>
              <path d="M19.4 15a1.65 1.65 0 0 0 .33 1.82l.06.06a2 2 0 0 1-2.83 2.83l-.06-.06a1.65 1.65 0 0 0-1.82-.33 1.65 1.65 0 0 0-1 1.51V21a2 2 0 0 1-4 0v-.09A1.65 1.65 0 0 0 9 19.4a1.65 1.65 0 0 0-1.82.33l-.06.06a2 2 0 0 1-2.83-2.83l.06-.06A1.65 1.65 0 0 0 4.68 15a1.65 1.65 0 0 0-1.51-1H3a2 2 0 0 1 0-4h.09A1.65 1.65 0 0 0 4.6 9a1.65 1.65 0 0 0-.33-1.82l-.06-.06a2 2 0 0 1 2.83-2.83l.06.06A1.65 1.65 0 0 0 9 4.68a1.65 1.65 0 0 0 1-1.51V3a2 2 0 0 1 4 0v.09a1.65 1.65 0 0 0 1 1.51 1.65 1.65 0 0 0 1.82-.33l.06-.06a2 2 0 0 1 2.83 2.83l-.06.06A1.65 1.65 0 0 0 19.4 9a1.65 1.65 0 0 0 1.51 1H21a2 2 0 0 1 0 4h-.09a1.65 1.65 0 0 0-1.51 1z"/>
            </svg>
          </button>
        </div>
      )}
    </nav>
  )
}
