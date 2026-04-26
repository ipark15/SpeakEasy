import { useEffect, useState } from "react"
import { useNavigate } from "react-router-dom"
import Navbar from "../components/Navbar"
import Card from "../components/Card"
import Button from "../components/Button"
import { useAuth } from "../hooks/useAuth"
import { supabase } from "../lib/supabase"

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
  onClick,
}: {
  label: string
  sub?: string
  right: React.ReactNode
  onClick?: () => void
}) {
  return (
    <div
      className={`flex items-center justify-between py-4 ${onClick ? "cursor-pointer" : ""}`}
      style={{ borderTop: "1px solid rgba(229,231,235,0.5)" }}
      onClick={onClick}
    >
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
  const { signOut } = useAuth()

  // ── Notifications ─────────────────────────────────────────────
  const [reminders, setReminders] = useState(() => localStorage.getItem("pref_reminders") !== "false")
  const [updates, setUpdates] = useState(() => localStorage.getItem("pref_updates") !== "false")
  useEffect(() => { localStorage.setItem("pref_reminders", String(reminders)) }, [reminders])
  useEffect(() => { localStorage.setItem("pref_updates", String(updates)) }, [updates])

  // ── Appearance ────────────────────────────────────────────────
  const [darkMode, setDarkMode] = useState(() => localStorage.getItem("pref_dark") === "true")
  useEffect(() => {
    localStorage.setItem("pref_dark", String(darkMode))
    document.documentElement.classList.toggle("dark", darkMode)
  }, [darkMode])

  // ── Microphone picker ─────────────────────────────────────────
  const [micDevices, setMicDevices] = useState<MediaDeviceInfo[]>([])
  const [selectedMicId, setSelectedMicId] = useState(() => localStorage.getItem("pref_mic_id") ?? "")
  const [showMicPicker, setShowMicPicker] = useState(false)

  async function openMicPicker() {
    if (showMicPicker) { setShowMicPicker(false); return }
    try {
      await navigator.mediaDevices.getUserMedia({ audio: true })
      const all = await navigator.mediaDevices.enumerateDevices()
      setMicDevices(all.filter((d) => d.kind === "audioinput"))
      setShowMicPicker(true)
    } catch {
      setMicDevices([])
      setShowMicPicker(true)
    }
  }

  function selectMic(deviceId: string) {
    setSelectedMicId(deviceId)
    localStorage.setItem("pref_mic_id", deviceId)
    setShowMicPicker(false)
  }

  function micLabel() {
    if (selectedMicId && micDevices.length > 0) {
      const dev = micDevices.find((d) => d.deviceId === selectedMicId)
      if (dev?.label) return dev.label
    }
    const stored = localStorage.getItem("pref_mic_id")
    return stored ? "Custom microphone selected" : "Default system microphone"
  }

  // ── Password change ───────────────────────────────────────────
  const [showPwForm, setShowPwForm] = useState(false)
  const [pwNew, setPwNew] = useState("")
  const [pwConfirm, setPwConfirm] = useState("")
  const [pwError, setPwError] = useState("")
  const [pwSaving, setPwSaving] = useState(false)
  const [pwSaved, setPwSaved] = useState(false)

  async function handlePasswordChange() {
    setPwError("")
    if (pwNew.length < 8) { setPwError("Password must be at least 8 characters"); return }
    if (pwNew !== pwConfirm) { setPwError("Passwords do not match"); return }
    setPwSaving(true)
    const { error } = await supabase.auth.updateUser({ password: pwNew })
    setPwSaving(false)
    if (error) {
      setPwError(error.message)
    } else {
      setPwSaved(true)
      setPwNew("")
      setPwConfirm("")
      setTimeout(() => { setPwSaved(false); setShowPwForm(false) }, 2000)
    }
  }

  async function handleSignOut() {
    await signOut()
    navigate("/")
  }

  return (
    <div className="min-h-screen bg-[#f5f3ff] dark:bg-[#0f0e1a]">
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
            Settings
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
            sub={micLabel()}
            right={
              <button
                onClick={(e) => { e.stopPropagation(); openMicPicker() }}
                className="text-[13px] font-semibold text-[#4338ca] hover:underline"
              >
                {showMicPicker ? "Cancel" : "Change"}
              </button>
            }
          />

          {showMicPicker && (
            <div className="flex flex-col gap-2 pb-3 pt-1">
              {micDevices.length === 0 ? (
                <p className="text-[13px] text-[#6a7282] px-1">
                  No microphone devices found. Check browser permissions.
                </p>
              ) : (
                micDevices.map((dev, i) => (
                  <button
                    key={dev.deviceId}
                    onClick={() => selectMic(dev.deviceId)}
                    className="w-full text-left px-4 py-2.5 rounded-[12px] text-[13px] transition-colors"
                    style={{
                      background: selectedMicId === dev.deviceId ? "#eef2ff" : "rgba(245,243,255,0.5)",
                      border: `1.5px solid ${selectedMicId === dev.deviceId ? "#4338ca" : "transparent"}`,
                      color: selectedMicId === dev.deviceId ? "#4338ca" : "#1e2939",
                      fontWeight: selectedMicId === dev.deviceId ? 600 : 400,
                    }}
                  >
                    {dev.label || `Microphone ${i + 1}`}
                  </button>
                ))
              )}
            </div>
          )}

          <SettingRow
            label="Recording Volume"
            sub="Controlled by system volume"
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

          {/* Change Password */}
          <SettingRow
            label="Change Password"
            sub={showPwForm ? "Enter a new password below" : undefined}
            onClick={() => setShowPwForm((v) => !v)}
            right={
              <svg
                width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="#9ca3af" strokeWidth="2.5"
                style={{ transform: showPwForm ? "rotate(90deg)" : "none", transition: "transform 0.15s" }}
              >
                <polyline points="9,18 15,12 9,6" />
              </svg>
            }
          />

          {showPwForm && (
            <div className="flex flex-col gap-3 pb-4 pt-1">
              <input
                type="password"
                placeholder="New password"
                value={pwNew}
                onChange={(e) => setPwNew(e.target.value)}
                className="w-full px-4 py-3 rounded-[14px] text-[14px] text-[#1e2939] outline-none transition-all"
                style={{ border: "1.5px solid rgba(229,231,235,0.8)", background: "white" }}
                onFocus={(e) => (e.target.style.borderColor = "#4338ca")}
                onBlur={(e) => (e.target.style.borderColor = "rgba(229,231,235,0.8)")}
              />
              <input
                type="password"
                placeholder="Confirm new password"
                value={pwConfirm}
                onChange={(e) => setPwConfirm(e.target.value)}
                className="w-full px-4 py-3 rounded-[14px] text-[14px] text-[#1e2939] outline-none transition-all"
                style={{ border: "1.5px solid rgba(229,231,235,0.8)", background: "white" }}
                onFocus={(e) => (e.target.style.borderColor = "#4338ca")}
                onBlur={(e) => (e.target.style.borderColor = "rgba(229,231,235,0.8)")}
              />
              {pwError && <p className="text-[12px] text-red-500">{pwError}</p>}
              <Button onClick={handlePasswordChange} disabled={pwSaving} className="w-full text-[13px] py-2.5">
                {pwSaved ? "Password updated!" : pwSaving ? "Updating…" : "Update Password"}
              </Button>
            </div>
          )}

          {/* Data & Privacy */}
          <SettingRow
            label="Data & Privacy"
            sub="Export data, manage your account"
            onClick={() => navigate("/settings/data")}
            right={
              <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="#9ca3af" strokeWidth="2.5">
                <polyline points="9,18 15,12 9,6" />
              </svg>
            }
          />

          {/* Sign Out */}
          <div className="py-4" style={{ borderTop: "1px solid rgba(229,231,235,0.5)" }}>
            <button
              onClick={handleSignOut}
              className="w-full flex items-center justify-between rounded-[14px] px-4 py-3 transition-colors text-left hover:opacity-80"
              style={{ background: "rgba(238,242,255,0.6)" }}
            >
              <div className="flex items-center gap-3">
                <svg width="15" height="15" viewBox="0 0 24 24" fill="none" stroke="#4338ca" strokeWidth="2">
                  <path d="M9 21H5a2 2 0 0 1-2-2V5a2 2 0 0 1 2-2h4" />
                  <polyline points="16,17 21,12 16,7" />
                  <line x1="21" y1="12" x2="9" y2="12" />
                </svg>
                <span className="text-[14px] font-medium text-[#4338ca]">Sign Out</span>
              </div>
              <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="#4338ca" strokeWidth="2.5">
                <polyline points="9,18 15,12 9,6" />
              </svg>
            </button>
          </div>

          {/* Delete Account */}
          <div className="pb-2" style={{ borderTop: "1px solid rgba(229,231,235,0.5)" }}>
            <button
              onClick={() => navigate("/settings/data")}
              className="w-full flex items-center justify-between rounded-[14px] px-4 py-3 transition-colors text-left hover:opacity-80 mt-2"
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
