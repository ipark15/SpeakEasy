import { useState } from "react"
import { useNavigate } from "react-router-dom"
import Navbar from "../components/Navbar"
import Card from "../components/Card"

function Toggle({ checked, onChange }: { checked: boolean; onChange: (v: boolean) => void }) {
  return (
    <button
      role="switch"
      aria-checked={checked}
      onClick={() => onChange(!checked)}
      className="relative w-11 h-6 rounded-full transition-colors flex-shrink-0"
      style={{ background: checked ? "#4338ca" : "#d1d5db" }}
    >
      <span
        className="absolute top-0.5 left-0.5 w-5 h-5 rounded-full bg-white shadow transition-transform"
        style={{ transform: checked ? "translateX(20px)" : "translateX(0)" }}
      />
    </button>
  )
}

function SettingRow({
  label,
  sub,
  right,
}: {
  label: string
  sub?: string
  right: React.ReactNode
}) {
  return (
    <div className="flex items-center justify-between py-4" style={{ borderTop: "1px solid rgba(229,231,235,0.5)" }}>
      <div>
        <p className="text-[14px] font-medium text-[#1e2939]">{label}</p>
        {sub && <p className="text-[12px] text-[#6a7282] mt-0.5">{sub}</p>}
      </div>
      {right}
    </div>
  )
}

export default function Settings() {
  const navigate = useNavigate()

  const [reminders, setReminders] = useState(true)
  const [updates, setUpdates] = useState(true)
  const [darkMode, setDarkMode] = useState(false)

  return (
    <div className="min-h-screen bg-[#f5f3ff]">
      <Navbar />
      <div className="max-w-[640px] mx-auto px-8 py-8 flex flex-col gap-6">

        {/* Back + heading */}
        <div>
          <button
            onClick={() => navigate("/dashboard")}
            className="flex items-center gap-2 text-[13px] text-[#6a7282] hover:text-[#4338ca] transition-colors mb-4"
          >
            <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.5">
              <polyline points="15,18 9,12 15,6" />
            </svg>
            Back to Dashboard
          </button>
          <p className="text-[11px] font-semibold tracking-[0.15em] text-[#6a7282] uppercase mb-2">Preferences</p>
          <h1 className="text-[32px] font-bold text-[#1e2939] font-['DM_Serif_Display'] leading-tight">
            Settings.
          </h1>
        </div>

        {/* Audio */}
        <Card>
          <div className="flex items-center gap-3 mb-2">
            <div className="w-10 h-10 rounded-xl bg-[#c7d2fe] flex items-center justify-center">
              <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="#4338ca" strokeWidth="2">
                <path d="M12 2a3 3 0 0 1 3 3v6a3 3 0 0 1-6 0V5a3 3 0 0 1 3-3z" />
                <path d="M19 10v1a7 7 0 0 1-14 0v-1" />
                <line x1="12" y1="18" x2="12" y2="22" />
              </svg>
            </div>
            <div>
              <p className="text-[10px] font-semibold tracking-widest text-[#6a7282] uppercase">Audio</p>
              <h3 className="text-[17px] font-bold text-[#1e2939]">Audio Settings</h3>
            </div>
          </div>

          <SettingRow
            label="Microphone Input"
            sub="Default system microphone"
            right={
              <button className="text-[13px] font-semibold text-[#4338ca] hover:underline">Change</button>
            }
          />
          <SettingRow
            label="Recording Volume"
            sub="Current: 75%"
            right={
              <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="#9ca3af" strokeWidth="2">
                <polygon points="11,5 6,9 2,9 2,15 6,15 11,19 11,5" />
                <path d="M15.54 8.46a5 5 0 0 1 0 7.07" />
                <path d="M19.07 4.93a10 10 0 0 1 0 14.14" />
              </svg>
            }
          />
        </Card>

        {/* Notifications */}
        <Card>
          <div className="flex items-center gap-3 mb-2">
            <div className="w-10 h-10 rounded-xl bg-[#bfdbfe] flex items-center justify-center">
              <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="#1d4ed8" strokeWidth="2">
                <path d="M18 8A6 6 0 0 0 6 8c0 7-3 9-3 9h18s-3-2-3-9" />
                <path d="M13.73 21a2 2 0 0 1-3.46 0" />
              </svg>
            </div>
            <div>
              <p className="text-[10px] font-semibold tracking-widest text-[#6a7282] uppercase">Alerts</p>
              <h3 className="text-[17px] font-bold text-[#1e2939]">Notifications</h3>
            </div>
          </div>

          <SettingRow
            label="Assessment Reminders"
            sub="Get reminded to practice regularly"
            right={<Toggle checked={reminders} onChange={setReminders} />}
          />
          <SettingRow
            label="Progress Updates"
            sub="Receive updates on your improvement"
            right={<Toggle checked={updates} onChange={setUpdates} />}
          />
        </Card>

        {/* Appearance */}
        <Card>
          <div className="flex items-center gap-3 mb-2">
            <div className="w-10 h-10 rounded-xl bg-[#fed7aa] flex items-center justify-center">
              <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="#c2410c" strokeWidth="2">
                <circle cx="12" cy="12" r="5" />
                <line x1="12" y1="1" x2="12" y2="3" /><line x1="12" y1="21" x2="12" y2="23" />
                <line x1="4.22" y1="4.22" x2="5.64" y2="5.64" /><line x1="18.36" y1="18.36" x2="19.78" y2="19.78" />
                <line x1="1" y1="12" x2="3" y2="12" /><line x1="21" y1="12" x2="23" y2="12" />
                <line x1="4.22" y1="19.78" x2="5.64" y2="18.36" /><line x1="18.36" y1="5.64" x2="19.78" y2="4.22" />
              </svg>
            </div>
            <div>
              <p className="text-[10px] font-semibold tracking-widest text-[#6a7282] uppercase">Display</p>
              <h3 className="text-[17px] font-bold text-[#1e2939]">Appearance</h3>
            </div>
          </div>

          <SettingRow
            label="Dark Mode"
            sub="Switch to dark theme"
            right={<Toggle checked={darkMode} onChange={setDarkMode} />}
          />
          <SettingRow
            label="Language"
            sub="English (US)"
            right={
              <button className="flex items-center gap-1 text-[13px] font-semibold text-[#4338ca] hover:underline">
                <svg width="13" height="13" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                  <circle cx="12" cy="12" r="10" />
                  <line x1="2" y1="12" x2="22" y2="12" />
                  <path d="M12 2a15.3 15.3 0 0 1 4 10 15.3 15.3 0 0 1-4 10 15.3 15.3 0 0 1-4-10 15.3 15.3 0 0 1 4-10z" />
                </svg>
                Change
              </button>
            }
          />
        </Card>

        {/* Privacy & Security */}
        <Card>
          <div className="flex items-center gap-3 mb-2">
            <div className="w-10 h-10 rounded-xl bg-[#f3f4f6] flex items-center justify-center">
              <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="#6b7280" strokeWidth="2">
                <rect x="3" y="11" width="18" height="11" rx="2" />
                <path d="M7 11V7a5 5 0 0 1 10 0v4" />
              </svg>
            </div>
            <div>
              <p className="text-[10px] font-semibold tracking-widest text-[#6a7282] uppercase">Security</p>
              <h3 className="text-[17px] font-bold text-[#1e2939]">Privacy & Security</h3>
            </div>
          </div>

          <SettingRow
            label="Change Password"
            right={
              <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="#9ca3af" strokeWidth="2.5">
                <polyline points="9,18 15,12 9,6" />
              </svg>
            }
          />
          <SettingRow
            label="Data & Privacy"
            right={
              <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="#9ca3af" strokeWidth="2.5">
                <polyline points="9,18 15,12 9,6" />
              </svg>
            }
          />
          <div className="py-4" style={{ borderTop: "1px solid rgba(229,231,235,0.5)" }}>
            <button
              className="w-full flex items-center justify-between rounded-[14px] px-4 py-3 transition-colors text-left"
              style={{ background: "rgba(254,242,242,0.6)" }}
            >
              <span className="text-[14px] font-medium text-red-500">Delete Account</span>
              <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="#ef4444" strokeWidth="2.5">
                <polyline points="9,18 15,12 9,6" />
              </svg>
            </button>
          </div>
        </Card>

      </div>
    </div>
  )
}
