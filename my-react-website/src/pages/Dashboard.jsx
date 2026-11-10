import { useEffect, useMemo, useState } from "react";

function Dashboard() {
  const [dashboard, setDashboard] = useState(null);
  const [context, setContext] = useState(null);

  const [loading, setLoading] = useState(true);
  const [processing, setProcessing] = useState(false);

  const [error, setError] = useState("");
  const [processMessage, setProcessMessage] = useState("");

  const [now, setNow] = useState(new Date());

  const getRollNo = (row) => {
    return (
      row.roll_no ||
      row.Roll_No ||
      row.roll ||
      row.Roll ||
      row.RollNo ||
      row["Roll No"] ||
      row["Roll Number"] ||
      row.student_id ||
      row.Student_ID ||
      "-"
    );
  };

  const getName = (row) => {
    return (
      row.name ||
      row.Name ||
      row.student_name ||
      row.Student_Name ||
      row["Student Name"] ||
      "-"
    );
  };

  const getStatus = (row) => {
    return (
      row.status ||
      row.Status ||
      row.attendance_status ||
      row["Attendance Status"] ||
      row.final_status ||
      row["Final Status"] ||
      row.Attendance ||
      row.attendance ||
      "-"
    );
  };

  const rows = useMemo(() => {
    if (!dashboard) return [];
    return Array.isArray(dashboard.rows) ? dashboard.rows : [];
  }, [dashboard]);

  const presentRows = useMemo(() => {
    return rows.filter((row) =>
      String(getStatus(row)).toLowerCase().includes("present")
    );
  }, [rows]);

  const absentRows = useMemo(() => {
    return rows.filter((row) =>
      String(getStatus(row)).toLowerCase().includes("absent")
    );
  }, [rows]);

  const loadDashboard = async () => {
    try {
      setLoading(true);
      setError("");

      const [dashboardResponse, contextResponse] = await Promise.allSettled([
        fetch("/api/dashboard"),
        fetch("/api/current-context"),
      ]);

      if (dashboardResponse.status === "fulfilled") {
        if (dashboardResponse.value.ok) {
          const data = await dashboardResponse.value.json();
          setDashboard(data);
        } else {
          setDashboard(null);
        }
      }

      if (contextResponse.status === "fulfilled") {
        if (contextResponse.value.ok) {
          const contextData = await contextResponse.value.json();
          setContext(contextData);
        } else {
          setContext(null);
        }
      }
    } catch (err) {
      console.error("Dashboard load failed:", err);
      setError("Could not load dashboard data from backend.");
    } finally {
      setLoading(false);
    }
  };

  const processCurrentPeriod = async () => {
    if (!context?.can_process || !context?.current_period) {
      setProcessMessage("Attendance is not recommended right now.");
      return;
    }

    try {
      setProcessing(true);
      setError("");
      setProcessMessage("");

      const response = await fetch("/api/process-period", {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
        },
        body: JSON.stringify({
          day: context.current_day,
          period: context.current_period,
          time: context.recommended_time || context.process_time || "",
        }),
      });

      const data = await response.json().catch(() => ({}));

      if (!response.ok || data.success === false) {
        throw new Error(
          data.error || data.stderr || data.message || "Processing failed."
        );
      }

      setProcessMessage(
        `${context.current_period} attendance processed successfully. Present: ${
          data.present ?? "-"
        }, Absent: ${data.absent ?? "-"}`
      );

      await loadDashboard();
    } catch (err) {
      console.error("Current period processing failed:", err);
      setError(err.message || "Current period processing failed.");
    } finally {
      setProcessing(false);
    }
  };

  useEffect(() => {
    loadDashboard();
  }, []);

  useEffect(() => {
    const timer = setInterval(() => {
      setNow(new Date());
    }, 1000);

    return () => clearInterval(timer);
  }, []);

  const displayDate =
    context?.display_date ||
    now.toLocaleDateString("en-IN", {
      weekday: "long",
      day: "2-digit",
      month: "long",
      year: "numeric",
    });

  const displayTime =
    context?.display_time ||
    now.toLocaleTimeString("en-IN", {
      hour: "2-digit",
      minute: "2-digit",
      second: "2-digit",
      hour12: true,
    });

  const recommendationText =
    context?.recommendation || "No recommendation available yet.";

  const recommendationTone = context?.can_process ? "success" : "warning";

  const totalStudents =
    dashboard?.total_students ?? rows.length ?? presentRows.length + absentRows.length;

  const presentCount = dashboard?.present ?? presentRows.length;
  const absentCount = dashboard?.absent ?? absentRows.length;

  const recognitionRate =
    dashboard?.recognition_rate ??
    (totalStudents > 0 ? ((presentCount / totalStudents) * 100).toFixed(2) : 0);

  return (
    <div className="page">
      <div className="dashboard-hero">
        <div>
          <p className="page-kicker">MAIN ADMIN DASHBOARD</p>
          <h1>Sreenidhi Smart Attendance</h1>
          <p>
            Monitor live class status, latest attendance, reports, and processing
            activity from one admin control panel.
          </p>
        </div>

        <div className="hero-actions">
          <button className="secondary-button" onClick={loadDashboard}>
            Refresh
          </button>

          <button
            className="primary-button"
            onClick={processCurrentPeriod}
            disabled={processing || !context?.can_process}
          >
            {processing ? "Processing..." : "Process Current Period"}
          </button>
        </div>
      </div>

      {error && (
        <div className="error-alert">
          <strong>Error:</strong> {error}
        </div>
      )}

      {processMessage && (
        <div className="success-alert">
          <strong>Success:</strong> {processMessage}
        </div>
      )}

      <div className="live-status-card dashboard-live-card">
        <div className="live-clock-block">
          <span className="live-icon">🕒</span>

          <div>
            <p>Live Date & Time</p>
            <h2>{displayTime}</h2>
            <span>{displayDate}</span>
          </div>
        </div>

        <div className="live-info-grid">
          <div>
            <p>Current Day</p>
            <strong>{context?.current_day || "-"}</strong>
          </div>

          <div>
            <p>Current Period</p>
            <strong>{context?.current_period || "No Period"}</strong>
          </div>

          <div>
            <p>Subject</p>
            <strong>{context?.current_subject || "-"}</strong>
          </div>

          <div>
            <p>Room</p>
            <strong>{context?.room || "-"}</strong>
          </div>
        </div>

        <span className={`recommendation-badge ${recommendationTone}`}>
          {recommendationText}
        </span>
      </div>

      <div className="stats-grid">
        <div className="stat-card">
          <div className="stat-icon">👥</div>
          <div>
            <p>Total Students</p>
            <h2>{loading ? "..." : totalStudents}</h2>
          </div>
        </div>

        <div className="stat-card success">
          <div className="stat-icon">✅</div>
          <div>
            <p>Present</p>
            <h2>{loading ? "..." : presentCount}</h2>
          </div>
        </div>

        <div className="stat-card danger">
          <div className="stat-icon">❌</div>
          <div>
            <p>Absent</p>
            <h2>{loading ? "..." : absentCount}</h2>
          </div>
        </div>

        <div className="stat-card info">
          <div className="stat-icon">📈</div>
          <div>
            <p>Recognition Rate</p>
            <h2>{loading ? "..." : `${recognitionRate}%`}</h2>
          </div>
        </div>
      </div>

      <div className="two-column-grid">
        <div className="content-card">
          <div className="section-title-row">
            <div>
              <h2>Latest Attendance</h2>
              <p>
                Latest file:{" "}
                <strong>{dashboard?.latest_file || "No file loaded yet"}</strong>
              </p>
            </div>

            {dashboard?.latest_file && (
              <a
                className="small-button"
                href={`/api/download/${dashboard.latest_file}`}
                target="_blank"
                rel="noreferrer"
              >
                Download
              </a>
            )}
          </div>

          {loading ? (
            <div className="empty-state">
              <div className="empty-icon">⏳</div>
              <h3>Loading latest attendance...</h3>
              <p>Please wait while dashboard data is loaded.</p>
            </div>
          ) : rows.length === 0 ? (
            <div className="empty-state">
              <div className="empty-icon">📊</div>
              <h3>No attendance file found yet</h3>
              <p>
                Go to Timetable Control and process a period. The latest report
                will appear here.
              </p>
            </div>
          ) : (
            <div className="reports-table-wrap">
              <table className="premium-table">
                <thead>
                  <tr>
                    <th>Roll Number</th>
                    <th>Student Name</th>
                    <th>Status</th>
                  </tr>
                </thead>

                <tbody>
                  {rows.slice(0, 12).map((row, index) => {
                    const status = getStatus(row);
                    const isPresent = String(status)
                      .toLowerCase()
                      .includes("present");

                    return (
                      <tr key={index}>
                        <td>
                          <strong>{getRollNo(row)}</strong>
                        </td>

                        <td>{getName(row)}</td>

                        <td>
                          <span
                            className={`status-badge ${
                              isPresent ? "success" : "danger"
                            }`}
                          >
                            {status}
                          </span>
                        </td>
                      </tr>
                    );
                  })}
                </tbody>
              </table>
            </div>
          )}
        </div>

        <div className="content-card">
          <div className="section-title-row">
            <div>
              <h2>Currently Present</h2>
              <p>Students marked present in the latest attendance file.</p>
            </div>

            <span className="pill-badge">{presentRows.length} present</span>
          </div>

          {presentRows.length === 0 ? (
            <div className="empty-state compact">
              <div className="empty-icon">👥</div>
              <h3>No present students to show</h3>
              <p>Process attendance first to populate this list.</p>
            </div>
          ) : (
            <div className="student-chip-list">
              {presentRows.map((row, index) => (
                <div className="student-chip" key={index}>
                  <span>✅</span>
                  <div>
                    <strong>{getRollNo(row)}</strong>
                    <p>{getName(row)}</p>
                  </div>
                </div>
              ))}
            </div>
          )}
        </div>
      </div>
    </div>
  );
}

export default Dashboard;