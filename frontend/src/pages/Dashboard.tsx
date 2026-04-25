import Navbar from "../components/Navbar"

export default function Dashboard() {
  return (
    <div className="min-h-screen bg-[#f5f3ff]">
      <Navbar />
      <div className="flex items-center justify-center h-[80vh]">
        <p className="text-[#6a7282] text-lg">Dashboard — Dev B</p>
      </div>
    </div>
  )
}
