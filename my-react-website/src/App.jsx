import { BrowserRouter, Routes, Route, Navigate } from "react-router-dom";

import Sidebar from "./components/Sidebar";
import Dashboard from "./pages/Dashboard";
import Timetable from "./pages/Timetable";
import CctvVideos from "./pages/CctvVideos";
import ProcessingJobs from "./pages/ProcessingJobs";
import AttendanceReports from "./pages/AttendanceReports";
import ManualEdit from "./pages/ManualEdit";
import Settings from "./pages/Settings";

import "./styles/dashboard.css";

function App() {
  return (
    <BrowserRouter>
      <div className="app-shell">
        <Sidebar />

        <main className="page-content">
          <Routes>
            <Route path="/" element={<Dashboard />} />
            <Route path="/timetable" element={<Timetable />} />
            <Route path="/cctv-videos" element={<CctvVideos />} />
            <Route path="/processing-jobs" element={<ProcessingJobs />} />
            <Route path="/attendance-reports" element={<AttendanceReports />} />
            <Route path="/manual-edit" element={<ManualEdit />} />
            <Route path="/settings" element={<Settings />} />

            <Route path="*" element={<Navigate to="/" replace />} />
          </Routes>
        </main>
      </div>
    </BrowserRouter>
  );
}

export default App;