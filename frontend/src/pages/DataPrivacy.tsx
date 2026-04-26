import { useState } from "react"
import { useNavigate } from "react-router-dom"
import Navbar from "../components/Navbar"
import Card from "../components/Card"
import Button from "../components/Button"
import { useAuth } from "../hooks/useAuth"

const BASE = import.meta.env.VITE_API_URL ?? "http://localhost:8000"

export default function DataPrivacy() {
  const navigate = useNavigate()
  const { user, signOut } = useAuth()

  const [showDeleteConfirm, setShowDeleteConfirm] = useState(false)
  const [deleteText, setDeleteText] = useState("")

  function downloadCsv() {
    if (!user) return
    window.open(`${BASE}/api/export/${user.id}/csv`, "_blank")
  }

  function downloadPdf() {
    if (!user) return
    window.open(`${BASE}/api/export/${user.id}/pdf`, "_blank")
  }

  async function handleDeleteAccount() {
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
            onClick={() => navigate("/settings")}
            className="flex items-center gap-2 text-[13px] text-[#6a7282] hover:text-[#4338ca] transition-colors mb-4"
          >
            <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.5">
              <polyline points="15,18 9,12 15,6" />
            </svg>
            Back to Settings
          </button>
          <p className="text-[11px] font-semibold tracking-[0.15em] text-[#6a7282] uppercase mb-2">Account</p>
          <h1 className="text-[32px] font-bold text-[#1e2939] font-['DM_Serif_Display'] leading-tight">
            Data & Privacy
          </h1>
        </div>

        {/* Export */}
        <Card>
          <div className="flex items-center gap-3 mb-4">
            <div className="w-10 h-10 rounded-xl bg-[#d1fae5] flex items-center justify-center">
              <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="#065f46" strokeWidth="2">
                <path d="M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4" />
                <polyline points="7,10 12,15 17,10" />
                <line x1="12" y1="15" x2="12" y2="3" />
              </svg>
            </div>
            <div>
              <p className="text-[10px] font-semibold tracking-widest text-[#6a7282] uppercase">Export</p>
              <h3 className="text-[17px] font-bold text-[#1e2939]">Your Data</h3>
            </div>
          </div>
          <p className="text-[13px] text-[#6a7282] leading-[20px] mb-5">
            Download a copy of all your speech session data, including scores, metrics, and coach conversations.
          </p>
          <div className="flex gap-3">
            <Button onClick={downloadCsv} variant="outline" className="flex-1 text-[13px] py-2.5">
              Download CSV
            </Button>
            <Button onClick={downloadPdf} variant="outline" className="flex-1 text-[13px] py-2.5">
              Download PDF Report
            </Button>
          </div>
        </Card>

        {/* Privacy info */}
        <Card>
          <div className="flex items-center gap-3 mb-4">
            <div className="w-10 h-10 rounded-xl bg-[#c7d2fe] flex items-center justify-center">
              <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="#4338ca" strokeWidth="2">
                <path d="M12 22s8-4 8-10V5l-8-3-8 3v7c0 6 8 10 8 10z" />
              </svg>
            </div>
            <div>
              <p className="text-[10px] font-semibold tracking-widest text-[#6a7282] uppercase">Privacy</p>
              <h3 className="text-[17px] font-bold text-[#1e2939]">How we handle your data</h3>
            </div>
          </div>
          <div className="flex flex-col gap-4">
            {[
              { title: "Audio stays local", desc: "Raw audio recordings are never uploaded to our servers or stored long-term." },
              { title: "Anonymized analysis", desc: "AI coaching agents receive numeric scores only — never your raw audio or transcript." },
              { title: "Secure storage", desc: "Session scores and progress are encrypted in Supabase with row-level security — only you can see your data." },
              { title: "No third-party sharing", desc: "Your data is never sold or shared with advertising networks." },
            ].map(({ title, desc }) => (
              <div key={title} className="flex items-start gap-3">
                <div className="w-5 h-5 rounded-full bg-[#eef2ff] flex items-center justify-center flex-shrink-0 mt-0.5">
                  <svg width="10" height="10" viewBox="0 0 24 24" fill="none" stroke="#4338ca" strokeWidth="3">
                    <polyline points="20,6 9,17 4,12" />
                  </svg>
                </div>
                <div>
                  <p className="text-[13px] font-semibold text-[#1e2939]">{title}</p>
                  <p className="text-[12px] text-[#6a7282] mt-0.5">{desc}</p>
                </div>
              </div>
            ))}
          </div>
        </Card>

        {/* Danger zone */}
        <Card>
          <div className="flex items-center gap-3 mb-4">
            <div className="w-10 h-10 rounded-xl bg-[#fee2e2] flex items-center justify-center">
              <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="#dc2626" strokeWidth="2">
                <polyline points="3,6 5,6 21,6" />
                <path d="M19,6l-1,14a2,2 0 0 1-2,2H8a2,2 0 0 1-2-2L5,6" />
                <path d="M10,11v6" /><path d="M14,11v6" />
                <path d="M9,6V4a1,1 0 0 1 1-1h4a1,1 0 0 1 1,1v2" />
              </svg>
            </div>
            <div>
              <p className="text-[10px] font-semibold tracking-widest text-[#6a7282] uppercase">Danger Zone</p>
              <h3 className="text-[17px] font-bold text-[#1e2939]">Delete Account</h3>
            </div>
          </div>
          <p className="text-[13px] text-[#6a7282] leading-[20px] mb-5">
            Permanently delete your account and all associated data. This action cannot be undone.
          </p>

          {!showDeleteConfirm ? (
            <button
              onClick={() => setShowDeleteConfirm(true)}
              className="w-full flex items-center justify-between rounded-[14px] px-4 py-3 hover:opacity-80 transition-opacity text-left"
              style={{ background: "rgba(254,242,242,0.8)", border: "1px solid rgba(239,68,68,0.2)" }}
            >
              <span className="text-[14px] font-medium text-red-500">Delete my account</span>
              <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="#ef4444" strokeWidth="2.5">
                <polyline points="9,18 15,12 9,6" />
              </svg>
            </button>
          ) : (
            <div
              className="flex flex-col gap-3 rounded-[16px] p-4"
              style={{ background: "rgba(254,242,242,0.6)", border: "1px solid rgba(239,68,68,0.2)" }}
            >
              <p className="text-[13px] font-semibold text-red-600">Are you sure? This cannot be undone.</p>
              <p className="text-[12px] text-[#6a7282]">
                Type <span className="font-mono font-bold text-[#1e2939]">delete</span> to confirm.
              </p>
              <input
                value={deleteText}
                onChange={(e) => setDeleteText(e.target.value)}
                placeholder="Type 'delete' to confirm"
                className="w-full px-4 py-3 rounded-[14px] text-[14px] outline-none"
                style={{ border: "1.5px solid rgba(239,68,68,0.4)", background: "white" }}
              />
              <div className="flex gap-3">
                <button
                  onClick={() => { setShowDeleteConfirm(false); setDeleteText("") }}
                  className="flex-1 px-4 py-2.5 rounded-[14px] text-[13px] font-medium text-[#6a7282] transition-colors hover:bg-[#f3f4f6]"
                  style={{ border: "1.5px solid rgba(229,231,235,0.8)", background: "white" }}
                >
                  Cancel
                </button>
                <button
                  onClick={handleDeleteAccount}
                  disabled={deleteText.toLowerCase() !== "delete"}
                  className="flex-1 px-4 py-2.5 rounded-[14px] text-[13px] font-medium text-white bg-red-500 hover:bg-red-600 transition-colors disabled:opacity-40 disabled:cursor-not-allowed"
                >
                  Delete Account
                </button>
              </div>
            </div>
          )}
        </Card>

      </div>
    </div>
  )
}
