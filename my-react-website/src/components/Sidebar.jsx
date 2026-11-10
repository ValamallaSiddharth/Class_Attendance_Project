import { NavLink } from "react-router-dom";
import { useState } from "react";

function Sidebar() {
  const [logoError, setLogoError] = useState(false);

  return (
    <aside className="sidebar">
      <div className="sidebar-brand">
        <div className="logo-shell">
          {!logoError ? (
            <img
              src="/su.png"
              alt="Sreenidhi University Logo"
              className="sidebar-logo"
              onError={() => setLogoError(true)}
            />
          ) : (
            <div className="logo-fallback">SU</div>
          )}
        </div>

        <div>
          <h2>Sreenidhi University</h2>
          <p>Smart Attendance Cell</p>
        </div>
      </div>

      <div className="admin-profile">
        <div className="admin-avatar">👨‍💻</div>

        <div>
          <h3>Main Admin</h3>
          <p>Attendance Controller</p>
        </div>
      </div>

      <p className="nav-heading">Navigation</p>

      <nav className="sidebar-nav">
        <NavLink to="/" end>
          <span>📊</span>
          Dashboard
        </NavLink>

        <NavLink to="/timetable">
          <span>📅</span>
          Timetable Control
        </NavLink>

        <NavLink to="/cctv-videos">
          <span>🎥</span>
          CCTV Videos
        </NavLink>

        <NavLink to="/processing-jobs">
          <span>⚡</span>
          Processing Jobs
        </NavLink>

        <NavLink to="/attendance-reports">
          <span>📄</span>
          Attendance Reports
        </NavLink>

        <NavLink to="/manual-edit">
          <span>✏️</span>
          Manual Edit
        </NavLink>

        <NavLink to="/settings">
          <span>⚙️</span>
          Settings
        </NavLink>
      </nav>

      <div className="server-status">
        <span className="status-dot"></span>

        <div>
          <strong>Server Active</strong>
          <p>python app.py</p>
        </div>
      </div>
    </aside>
  );
}

export default Sidebar;