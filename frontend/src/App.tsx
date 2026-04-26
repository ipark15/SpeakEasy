import { BrowserRouter, Routes, Route, Navigate } from "react-router-dom"
import { useAuth } from "./hooks/useAuth"
import Landing from "./pages/Landing"
import Dashboard from "./pages/Dashboard"
import Assess from "./pages/Assess"
import Results from "./pages/Results"
import CoachSelect from "./pages/CoachSelect"
import LiveSession from "./pages/LiveSession"
import History from "./pages/History"
import Profile from "./pages/Profile"
import Settings from "./pages/Settings"

function Guard({ children }: { children: React.ReactNode }) {
  const { user, loading } = useAuth()
  if (loading) return <div className="min-h-screen bg-[#f5f3ff]" />
  return user ? <>{children}</> : <Navigate to="/" replace />
}

export default function App() {
  return (
    <BrowserRouter>
      <Routes>
        <Route path="/" element={<Landing />} />
        <Route path="/dashboard" element={<Guard><Dashboard /></Guard>} />
        <Route path="/assess" element={<Guard><Assess /></Guard>} />
        <Route path="/results/:sessionId" element={<Guard><Results /></Guard>} />
        <Route path="/coach" element={<Guard><CoachSelect /></Guard>} />
        <Route path="/coach/:type" element={<Guard><LiveSession /></Guard>} />
        <Route path="/history" element={<Guard><History /></Guard>} />
        <Route path="/profile" element={<Guard><Profile /></Guard>} />
        <Route path="/settings" element={<Guard><Settings /></Guard>} />
      </Routes>
    </BrowserRouter>
  )
}
