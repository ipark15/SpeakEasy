import { BrowserRouter, Routes, Route, Navigate } from "react-router-dom"
import { useAuth } from "./hooks/useAuth"
import Landing from "./pages/Landing"
import Auth from "./pages/Auth"
import Dashboard from "./pages/Dashboard"
import Assess from "./pages/Assess"
import Results from "./pages/Results"
import History from "./pages/History"
import Profile from "./pages/Profile"
import Settings from "./pages/Settings"
import DataPrivacy from "./pages/DataPrivacy"

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
        <Route path="/auth" element={<Auth />} />
        <Route path="/dashboard" element={<Guard><Dashboard /></Guard>} />
        <Route path="/assess" element={<Guard><Assess /></Guard>} />
        <Route path="/results/:sessionId" element={<Guard><Results /></Guard>} />
        <Route path="/history" element={<Guard><History /></Guard>} />
        <Route path="/profile" element={<Guard><Profile /></Guard>} />
        <Route path="/settings" element={<Guard><Settings /></Guard>} />
        <Route path="/settings/data" element={<Guard><DataPrivacy /></Guard>} />
      </Routes>
    </BrowserRouter>
  )
}
