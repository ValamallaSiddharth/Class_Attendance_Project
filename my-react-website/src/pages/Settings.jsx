function Settings() {
  const attendanceRules = [
    {
      icon: "🎯",
      title: "Total Checkpoints",
      value: "5",
      description: "Attendance is checked at 5 checkpoint times per period.",
    },
    {
      icon: "✅",
      title: "Present Threshold",
      value: "3 out of 5",
      description:
        "A student is marked present if recognized in at least 3 checkpoints.",
    },
    {
      icon: "⏳",
      title: "Settling Time",
      value: "10 minutes",
      description:
        "The first 10 minutes of each period are ignored before attendance is recommended.",
    },
    {
      icon: "🎥",
      title: "Clip Duration",
      value: "10 seconds",
      description: "Each CCTV checkpoint clip is processed for 10 seconds.",
    },
  ];

  const systemDetails = [
    {
      label: "Backend Server",
      value: "python app.py",
    },
    {
      label: "Final Localhost",
      value: "http://127.0.0.1:5000",
    },
    {
      label: "Theory Room",
      value: "1106",
    },
    {
      label: "Lab Room",
      value: "1016",
    },
    {
      label: "Admin Role",
      value: "Main Admin",
    },
    {
      label: "University",
      value: "Sreenidhi University",
    },
  ];

  const periods = [
    ["P1", "09:00 - 09:50"],
    ["P2", "09:50 - 10:40"],
    ["P3", "10:50 - 11:40"],
    ["P4", "11:40 - 12:30"],
    ["Lunch", "12:30 - 13:20"],
    ["P6", "13:20 - 14:10"],
    ["P7", "14:20 - 15:10"],
    ["P8", "15:10 - 16:00"],
  ];

  return (
    <div className="page">
      <div className="page-header">
        <div>
          <p className="page-kicker">SYSTEM CONFIGURATION</p>
          <h1>Settings</h1>
          <p>
            View attendance rules, period timings, room details, and system
            configuration used by the admin dashboard.
          </p>
        </div>

        <button className="primary-button">System Ready</button>
      </div>

      <div className="settings-grid">
        {attendanceRules.map((rule) => (
          <div className="settings-card" key={rule.title}>
            <div className="settings-icon">{rule.icon}</div>

            <div>
              <p>{rule.title}</p>
              <h3>{rule.value}</h3>
              <span>{rule.description}</span>
            </div>
          </div>
        ))}
      </div>

      <div className="two-column-grid">
        <div className="content-card">
          <div className="section-title-row">
            <div>
              <h2>System Details</h2>
              <p>Core setup used by this attendance system.</p>
            </div>
          </div>

          <div className="settings-list">
            {systemDetails.map((item) => (
              <div className="settings-list-item" key={item.label}>
                <span>{item.label}</span>
                <strong>{item.value}</strong>
              </div>
            ))}
          </div>
        </div>

        <div className="content-card">
          <div className="section-title-row">
            <div>
              <h2>Period Timings</h2>
              <p>Official timetable slots used for recommendation logic.</p>
            </div>
          </div>

          <div className="period-list">
            {periods.map(([period, timing]) => (
              <div className="period-item" key={period}>
                <span>{period}</span>
                <strong>{timing}</strong>
              </div>
            ))}
          </div>
        </div>
      </div>

      <div className="content-card">
        <div className="section-title-row">
          <div>
            <h2>Processing Rules</h2>
            <p>How the system decides whether a student is present or absent.</p>
          </div>
        </div>

        <div className="rules-flow">
          <div className="rule-step">
            <span>1</span>
            <div>
              <h3>Ignore first 10 minutes</h3>
              <p>
                Students get time to settle before the system starts recommending
                attendance.
              </p>
            </div>
          </div>

          <div className="rule-step">
            <span>2</span>
            <div>
              <h3>Capture checkpoint clips</h3>
              <p>
                CCTV clips are processed at multiple checkpoints during the
                class period.
              </p>
            </div>
          </div>

          <div className="rule-step">
            <span>3</span>
            <div>
              <h3>Apply 3 out of 5 rule</h3>
              <p>
                A student must be recognized in at least 3 checkpoints to be
                marked present.
              </p>
            </div>
          </div>

          <div className="rule-step">
            <span>4</span>
            <div>
              <h3>Generate report</h3>
              <p>
                Final attendance is saved into CSV and Excel reports inside the
                exports folder.
              </p>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}

export default Settings;