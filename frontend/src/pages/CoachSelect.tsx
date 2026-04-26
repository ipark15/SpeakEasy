import { useNavigate } from "react-router-dom"
import Navbar from "../components/Navbar"

const COACHES = [
  {
    type: "fluency",
    label: "FLUENCY",
    name: "Fluency Coach",
    tagline: "Speak without hesitation",
    description: "Eliminate filler words and hesitations. Build the confidence to speak smoothly in any situation.",
    iconBg: "#c7d2fe",
    iconColor: "#4338ca",
    icon: (
      <svg width="22" height="22" viewBox="0 0 24 24" fill="none" stroke="#4338ca" strokeWidth="2">
        <path d="M21 15a2 2 0 0 1-2 2H7l-4 4V5a2 2 0 0 1 2-2h14a2 2 0 0 1 2 2z" />
      </svg>
    ),
  },
  {
    type: "clarity",
    label: "CLARITY",
    name: "Clarity Coach",
    tagline: "Every word, crystal clear",
    description: "Sharpen your articulation and reduce errors. Make every syllable land with precision and confidence.",
    iconBg: "#bfdbfe",
    iconColor: "#1d4ed8",
    icon: (
      <svg width="22" height="22" viewBox="0 0 24 24" fill="none" stroke="#1d4ed8" strokeWidth="2">
        <circle cx="11" cy="11" r="8" />
        <line x1="21" y1="21" x2="16.65" y2="16.65" />
      </svg>
    ),
  },
  {
    type: "rhythm",
    label: "RHYTHM",
    name: "Rhythm Coach",
    tagline: "Find your natural beat",
    description: "Master the timing and flow of speech. Develop a natural, confident rhythm that engages listeners.",
    iconBg: "#fed7aa",
    iconColor: "#c2410c",
    icon: (
      <svg width="22" height="22" viewBox="0 0 24 24" fill="none" stroke="#c2410c" strokeWidth="2">
        <polyline points="22,12 18,12 15,21 9,3 6,12 2,12" />
      </svg>
    ),
  },
  {
    type: "prosody",
    label: "PROSODY",
    name: "Prosody Coach",
    tagline: "Bring your voice to life",
    description: "Develop natural pitch variation and vocal expressiveness. Move beyond monotone to captivating speech.",
    iconBg: "#d1fae5",
    iconColor: "#065f46",
    icon: (
      <svg width="22" height="22" viewBox="0 0 24 24" fill="none" stroke="#065f46" strokeWidth="2">
        <path d="M9 18V5l12-2v13" />
        <circle cx="6" cy="18" r="3" />
        <circle cx="18" cy="16" r="3" />
      </svg>
    ),
  },
  {
    type: "pronunciation",
    label: "PRONUNCIATION",
    name: "Pronunciation Coach",
    tagline: "Perfect every sound",
    description: "Target specific sounds and words. Build accuracy and confidence in pronunciation one step at a time.",
    iconBg: "#ede9fe",
    iconColor: "#6d28d9",
    icon: (
      <svg width="22" height="22" viewBox="0 0 24 24" fill="none" stroke="#6d28d9" strokeWidth="2">
        <path d="M12 2a3 3 0 0 1 3 3v6a3 3 0 0 1-6 0V5a3 3 0 0 1 3-3z" />
        <path d="M19 10v1a7 7 0 0 1-14 0v-1" />
        <line x1="12" y1="18" x2="12" y2="22" />
        <line x1="8" y1="22" x2="16" y2="22" />
      </svg>
    ),
  },
]

export default function CoachSelect() {
  const navigate = useNavigate()

  return (
    <div className="min-h-screen bg-[#edeaf8]">
      <Navbar />
      <div className="max-w-[1088px] mx-auto px-8 py-10">

        {/* Header */}
        <div className="mb-10">
          <p className="text-[11px] font-semibold tracking-[0.15em] text-[#9896b0] uppercase mb-2">AI Coaching</p>
          <h1 className="text-[36px] font-bold text-[#1e1b4b] font-['DM_Serif_Display'] leading-tight mb-2">
            Choose your coach.
          </h1>
          <p className="text-[15px] text-[#6b6b8a]">Select a focus area and start a live guided session.</p>
        </div>

        {/* Coach grid */}
        <div className="grid grid-cols-3 gap-5">
          {COACHES.map((coach) => (
            <button
              key={coach.type}
              onClick={() => navigate(`/coach/${coach.type}`)}
              className="text-left group transition-transform hover:-translate-y-1"
              style={{
                background: "rgba(255,255,255,0.82)",
                border: "1.5px solid rgba(255,255,255,0.9)",
                borderRadius: 28,
                boxShadow: "0px 4px 12px rgba(99,102,241,0.08)",
                padding: "28px 28px 24px",
              }}
            >
              {/* Icon */}
              <div
                className="w-12 h-12 rounded-2xl flex items-center justify-center mb-5"
                style={{ background: coach.iconBg }}
              >
                {coach.icon}
              </div>

              {/* Label */}
              <p className="text-[10px] font-semibold tracking-[0.15em] text-[#9896b0] uppercase mb-1">
                {coach.label}
              </p>

              {/* Name */}
              <h3 className="text-[20px] font-bold text-[#1e1b4b] font-['DM_Serif_Display'] mb-1">
                {coach.name}
              </h3>

              {/* Tagline */}
              <p className="text-[13px] font-medium text-[#6b6b8a] mb-3">{coach.tagline}</p>

              {/* Description */}
              <p className="text-[13px] text-[#9896b0] leading-relaxed mb-6">{coach.description}</p>

              {/* CTA */}
              <div
                className="w-full flex items-center justify-center gap-2 py-3 rounded-[14px] font-medium text-[14px] transition-colors"
                style={{ background: "#4338ca", color: "white" }}
              >
                <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.5">
                  <polygon points="5,3 19,12 5,21 5,3" />
                </svg>
                Start Session
              </div>
            </button>
          ))}
        </div>

      </div>
    </div>
  )
}
