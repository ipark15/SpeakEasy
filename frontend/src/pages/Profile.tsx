import { useEffect, useRef, useState } from "react"
import { useNavigate } from "react-router-dom"
import Navbar from "../components/Navbar"
import Card from "../components/Card"
import Button from "../components/Button"
import { useAuth } from "../hooks/useAuth"
import { supabase } from "../lib/supabase"
import { getProfile, updateProfile, type ProfileData } from "../lib/api"

const BADGES = [
  {
    id: "first",
    name: "First Assessment",
    desc: "Completed your first speech test",
    iconBg: "#c7d2fe",
    icon: (
      <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="#4338ca" strokeWidth="2">
        <circle cx="12" cy="8" r="4" /><path d="M6 20v-2a6 6 0 0 1 12 0v2" />
      </svg>
    ),
    unlocked: true,
  },
  {
    id: "progress",
    name: "Progress Maker",
    desc: "Improved by 10+ points",
    iconBg: "#d1fae5",
    icon: (
      <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="#065f46" strokeWidth="2">
        <polyline points="22,7 13.5,15.5 8.5,10.5 2,17" /><polyline points="16,7 22,7 22,13" />
      </svg>
    ),
    unlocked: true,
  },
  {
    id: "consistent",
    name: "Consistent",
    desc: "Completed 10 assessments",
    iconBg: "#bfdbfe",
    icon: (
      <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="#1d4ed8" strokeWidth="2">
        <circle cx="12" cy="12" r="10" /><polyline points="12,6 12,12 16,14" />
      </svg>
    ),
    unlocked: true,
  },
  {
    id: "excellence",
    name: "Excellence",
    desc: "Score 95+ (Locked)",
    iconBg: "#f3f4f6",
    icon: (
      <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="#9ca3af" strokeWidth="2">
        <rect x="3" y="11" width="18" height="11" rx="2" /><path d="M7 11V7a5 5 0 0 1 10 0v4" />
      </svg>
    ),
    unlocked: false,
  },
]

export default function Profile() {
  const navigate = useNavigate()
  const { user } = useAuth()
  const nameInputRef = useRef<HTMLInputElement>(null)

  const [data, setData] = useState<ProfileData | null>(null)
  const [loadingProfile, setLoadingProfile] = useState(true)
  const [name, setName] = useState(() => localStorage.getItem("display_name") ?? "")
  const [saving, setSaving] = useState(false)
  const [saved, setSaved] = useState(false)

  // ── Password change ───────────────────────────────────────────
  const [pwNew, setPwNew] = useState("")
  const [pwConfirm, setPwConfirm] = useState("")
  const [pwError, setPwError] = useState("")
  const [pwSaving, setPwSaving] = useState(false)
  const [pwSaved, setPwSaved] = useState(false)

  useEffect(() => {
    if (!user) return
    if (!localStorage.getItem("display_name")) {
      setName(user.email?.split("@")[0] ?? "")
    }
    getProfile(user.id)
      .then((d) => {
        setData({ ...d, email: user.email ?? "" })
        // Only overwrite local name when the backend has a real saved value
        if (d.full_name) {
          setName(d.full_name)
          localStorage.setItem("display_name", d.full_name)
        }
      })
      .catch(() => {})
      .finally(() => setLoadingProfile(false))
  }, [user])

  async function handleSave() {
    if (!user) return
    setSaving(true)
    try {
      await updateProfile(user.id, { full_name: name })
      localStorage.setItem("display_name", name)
      setSaved(true)
      setTimeout(() => setSaved(false), 2000)
    } catch {
    } finally {
      setSaving(false)
    }
  }

  function handleEditProfile() {
    nameInputRef.current?.scrollIntoView({ behavior: "smooth", block: "center" })
    setTimeout(() => nameInputRef.current?.focus(), 300)
  }

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
      setTimeout(() => setPwSaved(false), 3000)
    }
  }

  const displayEmail = user?.email ?? ""

  return (
    <div className="min-h-screen bg-[#f5f3ff] dark:bg-[#0f0e1a]">
      <Navbar />
      <div className="max-w-[760px] mx-auto px-8 py-8 flex flex-col gap-6">

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
          <p className="text-[11px] font-semibold tracking-[0.15em] text-[#6a7282] uppercase mb-2">Profile</p>
          <h1 className="text-[32px] font-bold text-[#1e2939] font-['DM_Serif_Display'] leading-tight">
            My account
          </h1>
        </div>

        {/* User banner */}
        <div
          className="rounded-[24px] p-6 flex items-center justify-between"
          style={{ background: "#4338ca" }}
        >
          <div className="flex items-center gap-4">
            <div className="w-14 h-14 rounded-2xl bg-[rgba(255,255,255,0.2)] flex items-center justify-center">
              <svg width="26" height="26" viewBox="0 0 24 24" fill="none" stroke="white" strokeWidth="2">
                <circle cx="12" cy="8" r="4" /><path d="M6 20v-2a6 6 0 0 1 12 0v2" />
              </svg>
            </div>
            <div>
              <h2 className="text-[20px] font-bold text-white">{name || user?.email?.split("@")[0]}</h2>
              <p className="text-[13px] text-[rgba(255,255,255,0.75)] flex items-center gap-1 mt-0.5">
                <svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                  <path d="M4 4h16c1.1 0 2 .9 2 2v12c0 1.1-.9 2-2 2H4c-1.1 0-2-.9-2-2V6c0-1.1.9-2 2-2z" />
                  <polyline points="22,6 12,13 2,6" />
                </svg>
                {displayEmail}
              </p>
              <p className="text-[13px] text-[rgba(255,255,255,0.75)] flex items-center gap-1 mt-0.5">
                <svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                  <rect x="3" y="4" width="18" height="18" rx="2" />
                  <line x1="16" y1="2" x2="16" y2="6" /><line x1="8" y1="2" x2="8" y2="6" />
                  <line x1="3" y1="10" x2="21" y2="10" />
                </svg>
                Joined {data.joined_at}
              </p>
            </div>
          </div>
          <button
            onClick={handleEditProfile}
            className="px-4 py-2 rounded-[12px] text-[13px] font-semibold text-[#4338ca] bg-white hover:bg-[#f5f3ff] transition-colors"
          >
            Edit Profile
          </button>
        </div>

        {/* Stats */}
        {loadingProfile ? (
          <div className="grid grid-cols-3 gap-4">
            {[0, 1, 2].map(i => <div key={i} className="h-24 rounded-[24px] bg-[#e0daf7] animate-pulse" />)}
          </div>
        ) : (
        <div className="grid grid-cols-3 gap-4">
          {[
            { label: "Best Score", value: data?.best_score ?? 0, sub: "All time", iconBg: "#c7d2fe", stroke: "#4338ca" },
            { label: "Improvement", value: `+${data?.improvement ?? 0}`, sub: "Points gained", iconBg: "#d1fae5", stroke: "#065f46" },
            { label: "Total Tests", value: data?.total_tests ?? 0, sub: "Sessions done", iconBg: "#bfdbfe", stroke: "#1d4ed8" },
          ].map(({ label, value, sub, iconBg, stroke }) => (
            <Card key={label}>
              <div className="w-9 h-9 rounded-xl flex items-center justify-center mb-3" style={{ background: iconBg }}>
                <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke={stroke} strokeWidth="2">
                  <polyline points="22,7 13.5,15.5 8.5,10.5 2,17" /><polyline points="16,7 22,7 22,13" />
                </svg>
              </div>
              <p className="text-[10px] font-semibold tracking-widest text-[#6a7282] uppercase mb-1">{label}</p>
              <p className="text-[28px] font-bold text-[#1e2939]">{value}</p>
              <p className="text-[12px] text-[#9ca3af]">{sub}</p>
            </Card>
          ))}
        </div>
        )}

        {/* Achievements */}
        <Card>
          <p className="text-[10px] font-semibold tracking-[0.15em] text-[#6a7282] uppercase mb-1">Achievements</p>
          <h3 className="text-[20px] font-bold text-[#1e2939] font-['DM_Serif_Display'] mb-5">Badges earned</h3>
          <div className="grid grid-cols-2 gap-3">
            {BADGES.map((badge) => (
              <div
                key={badge.id}
                className={`flex items-center gap-3 rounded-[16px] p-4 ${badge.unlocked ? "" : "opacity-50"}`}
                style={{ background: "rgba(245,243,255,0.5)" }}
              >
                <div
                  className="w-10 h-10 rounded-xl flex items-center justify-center flex-shrink-0"
                  style={{ background: badge.iconBg }}
                >
                  {badge.icon}
                </div>
                <div>
                  <p className="text-[14px] font-semibold text-[#1e2939]">{badge.name}</p>
                  <p className="text-[12px] text-[#6a7282]">{badge.desc}</p>
                </div>
              </div>
            ))}
          </div>
        </Card>

        {/* Personal info */}
        <Card>
          <p className="text-[10px] font-semibold tracking-[0.15em] text-[#6a7282] uppercase mb-1">Account Info</p>
          <h3 className="text-[20px] font-bold text-[#1e2939] font-['DM_Serif_Display'] mb-5">Personal information</h3>
          <div className="flex flex-col gap-4">
            <div>
              <label className="text-[11px] font-semibold tracking-widest text-[#6a7282] uppercase block mb-2">
                Display Name
              </label>
              <input
                ref={nameInputRef}
                value={name}
                onChange={(e) => setName(e.target.value)}
                className="w-full px-4 py-3 rounded-[14px] text-[14px] text-[#1e2939] outline-none transition-all"
                style={{ border: "1.5px solid rgba(229,231,235,0.8)", background: "white" }}
                onFocus={(e) => (e.target.style.borderColor = "#4338ca")}
                onBlur={(e) => (e.target.style.borderColor = "rgba(229,231,235,0.8)")}
              />
            </div>
            <div>
              <label className="text-[11px] font-semibold tracking-widest text-[#6a7282] uppercase block mb-2">
                Email
              </label>
              <input
                value={displayEmail}
                readOnly
                className="w-full px-4 py-3 rounded-[14px] text-[14px] text-[#9ca3af] bg-[#f9fafb]"
                style={{ border: "1.5px solid rgba(229,231,235,0.5)" }}
              />
              <p className="text-[11px] text-[#9ca3af] mt-1.5">Email cannot be changed after signup</p>
            </div>
            <Button onClick={handleSave} disabled={saving} className="w-full">
              {saved ? "Saved!" : saving ? "Saving…" : "Save Changes"}
            </Button>
          </div>
        </Card>

        {/* Change Password */}
        <Card>
          <p className="text-[10px] font-semibold tracking-[0.15em] text-[#6a7282] uppercase mb-1">Security</p>
          <h3 className="text-[20px] font-bold text-[#1e2939] font-['DM_Serif_Display'] mb-5">Change password</h3>
          <div className="flex flex-col gap-4">
            <div>
              <label className="text-[11px] font-semibold tracking-widest text-[#6a7282] uppercase block mb-2">
                New Password
              </label>
              <input
                type="password"
                placeholder="At least 8 characters"
                value={pwNew}
                onChange={(e) => setPwNew(e.target.value)}
                className="w-full px-4 py-3 rounded-[14px] text-[14px] text-[#1e2939] outline-none transition-all"
                style={{ border: "1.5px solid rgba(229,231,235,0.8)", background: "white" }}
                onFocus={(e) => (e.target.style.borderColor = "#4338ca")}
                onBlur={(e) => (e.target.style.borderColor = "rgba(229,231,235,0.8)")}
              />
            </div>
            <div>
              <label className="text-[11px] font-semibold tracking-widest text-[#6a7282] uppercase block mb-2">
                Confirm New Password
              </label>
              <input
                type="password"
                placeholder="Re-enter new password"
                value={pwConfirm}
                onChange={(e) => setPwConfirm(e.target.value)}
                className="w-full px-4 py-3 rounded-[14px] text-[14px] text-[#1e2939] outline-none transition-all"
                style={{ border: "1.5px solid rgba(229,231,235,0.8)", background: "white" }}
                onFocus={(e) => (e.target.style.borderColor = "#4338ca")}
                onBlur={(e) => (e.target.style.borderColor = "rgba(229,231,235,0.8)")}
              />
            </div>
            {pwError && <p className="text-[12px] text-red-500">{pwError}</p>}
            {pwSaved && <p className="text-[12px] text-green-600 font-medium">Password updated successfully</p>}
            <Button onClick={handlePasswordChange} disabled={pwSaving} className="w-full">
              {pwSaving ? "Updating…" : "Update Password"}
            </Button>
          </div>
        </Card>

      </div>
    </div>
  )
}
