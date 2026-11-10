import { useEffect, useState } from "react";

function ManualEdit() {
  const [rows, setRows] = useState([]);
  const [latestFile, setLatestFile] = useState("");
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);

  const [message, setMessage] = useState("");
  const [error, setError] = useState("");

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
      "Absent"
    );
  };

  const loadLatestAttendance = async () => {
    try {
      setLoading(true);
      setError("");
      setMessage("");

      const response = await fetch("/api/attendance/latest");

      if (!response.ok) {
        setRows([]);
        setLatestFile("");
        setError("No latest attendance file found yet.");
        return;
      }

      const data = await response.json();

      setRows(Array.isArray(data.rows) ? data.rows : []);
      setLatestFile(data.latest_file || data.file || "");
    } catch (err) {
      console.error("Failed to load latest attendance:", err);
      setRows([]);
      setLatestFile("");
      setError("Could not load latest attendance data.");
    } finally {
      setLoading(false);
    }
  };

  const updateStatus = (index, newStatus) => {
    setRows((previousRows) =>
      previousRows.map((row, rowIndex) => {
        if (rowIndex !== index) return row;

        return {
          ...row,
          Status: newStatus,
          status: newStatus,
          attendance_status: newStatus,
        };
      })
    );
  };

  const saveEditedCopy = async () => {
    try {
      setSaving(true);
      setError("");
      setMessage("");

      const response = await fetch("/api/manual-edit", {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
        },
        body: JSON.stringify({
          source_file: latestFile,
          rows,
        }),
      });

      const data = await response.json().catch(() => ({}));

      if (!response.ok || data.success === false) {
        throw new Error(data.error || "Failed to save edited attendance file.");
      }

      setMessage(
        `Edited attendance saved successfully as ${
          data.edited_file || "new edited CSV file"
        }.`
      );
    } catch (err) {
      console.error("Failed to save manual edit:", err);
      setError(err.message || "Failed to save manual edit.");
    } finally {
      setSaving(false);
    }
  };

  useEffect(() => {
    loadLatestAttendance();
  }, []);

  return (
    <div className="page">
      <div className="page-header">
        <div>
          <p className="page-kicker">ADMIN CORRECTION PANEL</p>
          <h1>Manual Edit</h1>
          <p>
            Review latest attendance records and save corrections without
            overwriting the original report.
          </p>
        </div>

        <button className="primary-button" onClick={loadLatestAttendance}>
          Refresh Latest
        </button>
      </div>

      <div className="warning-card">
        <div className="warning-icon">🛡️</div>

        <div>
          <h3>Original report is protected</h3>
          <p>
            Manual corrections will be saved as a new edited file. The original
            CSV will not be overwritten.
          </p>
        </div>
      </div>

      {message && <div className="success-alert">{message}</div>}
      {error && <div className="error-alert">{error}</div>}

      <div className="info-grid">
        <div className="info-card">
          <span>📄</span>
          <div>
            <h3>{latestFile || "None"}</h3>
            <p>Latest File</p>
          </div>
        </div>

        <div className="info-card">
          <span>👥</span>
          <div>
            <h3>{rows.length}</h3>
            <p>Total Records</p>
          </div>
        </div>

        <div className="info-card">
          <span>✅</span>
          <div>
            <h3>
              {
                rows.filter((row) =>
                  String(getStatus(row)).toLowerCase().includes("present")
                ).length
              }
            </h3>
            <p>Present</p>
          </div>
        </div>

        <div className="info-card">
          <span>❌</span>
          <div>
            <h3>
              {
                rows.filter((row) =>
                  String(getStatus(row)).toLowerCase().includes("absent")
                ).length
              }
            </h3>
            <p>Absent</p>
          </div>
        </div>
      </div>

      <div className="content-card">
        <div className="section-title-row">
          <div>
            <h2>Editable Attendance Records</h2>
            <p>Change only the attendance status where required.</p>
          </div>

          <button
            className="primary-button"
            onClick={saveEditedCopy}
            disabled={saving || rows.length === 0}
          >
            {saving ? "Saving..." : "Save Edited Copy"}
          </button>
        </div>

        {loading ? (
          <div className="empty-state">
            <div className="empty-icon">⏳</div>
            <h3>Loading attendance...</h3>
            <p>Please wait while the latest attendance file is loaded.</p>
          </div>
        ) : rows.length === 0 ? (
          <div className="empty-state">
            <div className="empty-icon">✏️</div>
            <h3>No attendance data available</h3>
            <p>
              Process a period first from Timetable Control. Then manual editing
              will become available here.
            </p>
          </div>
        ) : (
          <div className="reports-table-wrap">
            <table className="premium-table">
              <thead>
                <tr>
                  <th>Roll Number</th>
                  <th>Student Name</th>
                  <th>Current Status</th>
                  <th>Edit Status</th>
                </tr>
              </thead>

              <tbody>
                {rows.map((row, index) => {
                  const currentStatus = getStatus(row);
                  const isPresent = String(currentStatus)
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
                          {currentStatus}
                        </span>
                      </td>

                      <td>
                        <select
                          className="status-select"
                          value={isPresent ? "Present" : "Absent"}
                          onChange={(event) =>
                            updateStatus(index, event.target.value)
                          }
                        >
                          <option value="Present">Present</option>
                          <option value="Absent">Absent</option>
                        </select>
                      </td>
                    </tr>
                  );
                })}
              </tbody>
            </table>
          </div>
        )}
      </div>
    </div>
  );
}

export default ManualEdit;