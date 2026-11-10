import { useEffect, useMemo, useState } from "react";

const DAYS = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday"];

const PERIOD_TIMINGS = {
  P1: { start: "09:00", end: "09:50", processTime: "09:20" },
  P2: { start: "09:50", end: "10:40", processTime: "10:10" },
  P3: { start: "10:50", end: "11:40", processTime: "11:10" },
  P4: { start: "11:40", end: "12:30", processTime: "12:00" },
  Lunch: { start: "12:30", end: "13:20", processTime: "" },
  P6: { start: "13:20", end: "14:10", processTime: "13:40" },
  P7: { start: "14:20", end: "15:10", processTime: "14:40" },
  P8: { start: "15:10", end: "16:00", processTime: "15:30" },
};

const TIMETABLE = {
  Monday: [
    { period: "P1", subject: "SWE", room: "1106", type: "Theory" },
    { period: "P2", subject: "SWE", room: "1106", type: "Theory" },
    { period: "P3", subject: "CCM/CVO", room: "1016", type: "Lab" },
    { period: "P4", subject: "CCM/CVO", room: "1016", type: "Lab" },
    { period: "Lunch", subject: "Lunch Break", room: "-", type: "Break" },
    { period: "P6", subject: "SWE", room: "1106", type: "Theory" },
    { period: "P7", subject: "CCM/CVO", room: "1106", type: "Theory" },
    { period: "P8", subject: "CCM/CVO", room: "1106", type: "Theory" },
  ],
  Tuesday: [
    { period: "P1", subject: "CCM/CVO", room: "1106", type: "Theory" },
    { period: "P2", subject: "CCM/CVO", room: "1106", type: "Theory" },
    { period: "P3", subject: "SWE", room: "1106", type: "Theory" },
    { period: "P4", subject: "SWE", room: "1106", type: "Theory" },
    { period: "Lunch", subject: "Lunch Break", room: "-", type: "Break" },
    { period: "P6", subject: "CCM/CVO", room: "1106", type: "Theory" },
    { period: "P7", subject: "SWE", room: "1016", type: "Lab" },
    { period: "P8", subject: "SWE", room: "1016", type: "Lab" },
  ],
  Wednesday: [
    { period: "P1", subject: "SWE", room: "1106", type: "Theory" },
    { period: "P2", subject: "SWE", room: "1106", type: "Theory" },
    { period: "P3", subject: "CCM/CVO", room: "1106", type: "Theory" },
    { period: "P4", subject: "CCM/CVO", room: "1106", type: "Theory" },
    { period: "Lunch", subject: "Lunch Break", room: "-", type: "Break" },
    { period: "P6", subject: "SWE", room: "1106", type: "Theory" },
    { period: "P7", subject: "CCM/CVO", room: "1016", type: "Lab" },
    { period: "P8", subject: "CCM/CVO", room: "1016", type: "Lab" },
  ],
  Thursday: [
    { period: "P1", subject: "CCM/CVO", room: "1106", type: "Theory" },
    { period: "P2", subject: "CCM/CVO", room: "1106", type: "Theory" },
    { period: "P3", subject: "SWE", room: "1106", type: "Theory" },
    { period: "P4", subject: "SWE", room: "1106", type: "Theory" },
    { period: "Lunch", subject: "Lunch Break", room: "-", type: "Break" },
    { period: "P6", subject: "CCM/CVO", room: "1106", type: "Theory" },
    { period: "P7", subject: "SWE", room: "1016", type: "Lab" },
    { period: "P8", subject: "SWE", room: "1016", type: "Lab" },
  ],
  Friday: [
    { period: "P1", subject: "SWE", room: "1106", type: "Theory" },
    { period: "P2", subject: "SWE", room: "1106", type: "Theory" },
    { period: "P3", subject: "CCM/CVO", room: "1106", type: "Theory" },
    { period: "P4", subject: "CCM/CVO", room: "1106", type: "Theory" },
    { period: "Lunch", subject: "Lunch Break", room: "-", type: "Break" },
    { period: "P6", subject: "SWE", room: "1106", type: "Theory" },
    { period: "P7", subject: "CCM/CVO", room: "1106", type: "Theory" },
    { period: "P8", subject: "SWE/CCM/CVO", room: "1106", type: "Theory" },
  ],
  Saturday: [],
};

const SUBJECT_DETAILS = {
  SWE: {
    fullName: "Software Engineering",
    faculty: "Dr. Keerthi G",
  },
  "CCM/CVO": {
    fullName: "Cloud Computing / Computer Vision through OpenCV",
    faculty: "Dr. Pranayanath Reddy A / Mr. Vikas B",
  },
  "SWE/CCM/CVO": {
    fullName: "Software Engineering / Cloud Computing / Computer Vision",
    faculty: "Dr. Keerthi G / Dr. Pranayanath Reddy A / Mr. Vikas B",
  },
};

function timeToMinutes(time) {
  if (!time) return -1;

  const [hours, minutes] = time.split(":").map(Number);
  return hours * 60 + minutes;
}

function getTodayName() {
  return new Date().toLocaleDateString("en-US", { weekday: "long" });
}

function getCurrentTimeText(date) {
  return date.toLocaleTimeString("en-IN", {
    hour: "2-digit",
    minute: "2-digit",
    second: "2-digit",
    hour12: true,
  });
}

function getCurrentDateText(date) {
  return date.toLocaleDateString("en-IN", {
    weekday: "long",
    day: "2-digit",
    month: "long",
    year: "numeric",
  });
}

function findCurrentPeriod() {
  const now = new Date();
  const currentMinutes = now.getHours() * 60 + now.getMinutes();

  for (const [period, timing] of Object.entries(PERIOD_TIMINGS)) {
    const start = timeToMinutes(timing.start);
    const end = timeToMinutes(timing.end);

    if (currentMinutes >= start && currentMinutes < end) {
      return period;
    }
  }

  return null;
}

function getFrontendRecommendation(period) {
  if (!period) {
    return {
      text: "No active class period right now.",
      tone: "danger",
      canProcess: false,
    };
  }

  if (period === "Lunch") {
    return {
      text: "Lunch break. Attendance not required.",
      tone: "warning",
      canProcess: false,
    };
  }

  const now = new Date();
  const currentMinutes = now.getHours() * 60 + now.getMinutes();
  const startMinutes = timeToMinutes(PERIOD_TIMINGS[period].start);

  if (currentMinutes < startMinutes + 10) {
    return {
      text: "Wait for settling time before taking attendance.",
      tone: "warning",
      canProcess: false,
    };
  }

  return {
    text: "Recommended: take attendance now.",
    tone: "success",
    canProcess: true,
  };
}

function Timetable() {
  const todayName = getTodayName();
  const defaultDay = DAYS.includes(todayName) ? todayName : "Monday";

  const [selectedDay, setSelectedDay] = useState(defaultDay);
  const [now, setNow] = useState(new Date());

  const [periodStatus, setPeriodStatus] = useState({});
  const [processingKey, setProcessingKey] = useState("");
  const [result, setResult] = useState(null);
  const [errorResult, setErrorResult] = useState(null);

  const currentPeriod = useMemo(() => findCurrentPeriod(), [now]);
  const recommendation = useMemo(
    () => getFrontendRecommendation(currentPeriod),
    [currentPeriod]
  );

  const selectedRows = TIMETABLE[selectedDay] || [];

  const currentSubjectRow =
    TIMETABLE[defaultDay]?.find((row) => row.period === currentPeriod) || null;

  useEffect(() => {
    const timer = setInterval(() => {
      setNow(new Date());
    }, 1000);

    return () => clearInterval(timer);
  }, []);

  const processAttendance = async (row) => {
    if (row.period === "Lunch") return;

    const timing = PERIOD_TIMINGS[row.period];
    const key = `${selectedDay}-${row.period}`;

    try {
      setProcessingKey(key);
      setErrorResult(null);
      setResult(null);

      setPeriodStatus((previous) => ({
        ...previous,
        [key]: "processing",
      }));

      const response = await fetch("/api/process-period", {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
        },
        body: JSON.stringify({
          day: selectedDay,
          period: row.period,
          time: timing.processTime,
        }),
      });

      const data = await response.json().catch(() => ({}));

      if (!response.ok || data.success === false) {
        throw new Error(
          data.error ||
            data.stderr ||
            data.message ||
            "Attendance processing failed."
        );
      }

      setResult({
        ...data,
        day: selectedDay,
        period: row.period,
        subject: row.subject,
        time: timing.processTime,
      });

      setPeriodStatus((previous) => ({
        ...previous,
        [key]: "done",
      }));
    } catch (error) {
      console.error("Processing failed:", error);

      setErrorResult({
        day: selectedDay,
        period: row.period,
        subject: row.subject,
        message: error.message || "Unknown processing error",
      });

      setPeriodStatus((previous) => ({
        ...previous,
        [key]: "failed",
      }));
    } finally {
      setProcessingKey("");
    }
  };

  const processCurrentPeriod = () => {
    if (!currentPeriod || currentPeriod === "Lunch") return;

    const currentRow = TIMETABLE[defaultDay]?.find(
      (row) => row.period === currentPeriod
    );

    if (!currentRow) return;

    setSelectedDay(defaultDay);

    setTimeout(() => {
      processAttendance(currentRow);
    }, 100);
  };

  const getStatusBadge = (row) => {
    if (row.period === "Lunch") {
      return <span className="status-badge warning">Lunch</span>;
    }

    const key = `${selectedDay}-${row.period}`;
    const status = periodStatus[key];

    if (status === "processing") {
      return <span className="status-badge warning">Processing</span>;
    }

    if (status === "done") {
      return <span className="status-badge success">Already Done</span>;
    }

    if (status === "failed") {
      return <span className="status-badge danger">Failed</span>;
    }

    return <span className="status-badge neutral">Pending</span>;
  };

  return (
    <div className="page">
      <div className="page-header">
        <div>
          <p className="page-kicker">ADMIN PERIOD CONTROL</p>
          <h1>Timetable Control</h1>
          <p>
            Select a day, review the class timetable, and process attendance for
            each period.
          </p>
        </div>

        <button
          className="primary-button"
          onClick={processCurrentPeriod}
          disabled={!recommendation.canProcess}
        >
          Process Current Period
        </button>
      </div>

      <div className="live-status-card">
        <div className="live-clock-block">
          <span className="live-icon">🕒</span>

          <div>
            <p>Current Date & Time</p>
            <h2>{getCurrentTimeText(now)}</h2>
            <span>{getCurrentDateText(now)}</span>
          </div>
        </div>

        <div className="live-info-grid">
          <div>
            <p>Current Day</p>
            <strong>{defaultDay}</strong>
          </div>

          <div>
            <p>Current Period</p>
            <strong>{currentPeriod || "No Period"}</strong>
          </div>

          <div>
            <p>Current Subject</p>
            <strong>{currentSubjectRow?.subject || "-"}</strong>
          </div>

          <div>
            <p>Room</p>
            <strong>{currentSubjectRow?.room || "-"}</strong>
          </div>
        </div>

        <span className={`recommendation-badge ${recommendation.tone}`}>
          {recommendation.text}
        </span>
      </div>

      <div className="day-tabs">
        {DAYS.map((day) => (
          <button
            key={day}
            className={selectedDay === day ? "active" : ""}
            onClick={() => {
              setSelectedDay(day);
              setResult(null);
              setErrorResult(null);
            }}
          >
            {day}
            {day === defaultDay && <span>Today</span>}
          </button>
        ))}
      </div>

      {result && (
        <div className="result-card success-result">
          <div>
            <p className="page-kicker">PROCESSING COMPLETED</p>
            <h2>
              {result.day} {result.period} · {result.subject}
            </h2>
            <p>
              Latest file: <strong>{result.latest_file || "Generated report"}</strong>
            </p>
          </div>

          <div className="result-stats">
            <div>
              <span>Total</span>
              <strong>{result.total_students ?? "-"}</strong>
            </div>

            <div>
              <span>Present</span>
              <strong>{result.present ?? "-"}</strong>
            </div>

            <div>
              <span>Absent</span>
              <strong>{result.absent ?? "-"}</strong>
            </div>

            <div>
              <span>Rate</span>
              <strong>{result.recognition_rate ?? "-"}%</strong>
            </div>
          </div>
        </div>
      )}

      {errorResult && (
        <div className="result-card error-result">
          <div>
            <p className="page-kicker">PROCESSING FAILED</p>
            <h2>
              {errorResult.day} {errorResult.period} · {errorResult.subject}
            </h2>
            <p>{errorResult.message}</p>
          </div>
        </div>
      )}

      <div className="content-card">
        <div className="section-title-row">
          <div>
            <h2>{selectedDay} Timetable</h2>
            <p>
              Period-wise control panel with room, subject, faculty, and
              processing actions.
            </p>
          </div>

          <span className="pill-badge">
            {selectedRows.length > 0
              ? `${selectedRows.length} slots`
              : "No timetable"}
          </span>
        </div>

        {selectedRows.length === 0 ? (
          <div className="empty-state">
            <div className="empty-icon">📅</div>
            <h3>No timetable scheduled</h3>
            <p>
              There are no regular class periods configured for this day yet.
            </p>
          </div>
        ) : (
          <div className="reports-table-wrap">
            <table className="premium-table timetable-table">
              <thead>
                <tr>
                  <th>Period</th>
                  <th>Time</th>
                  <th>Subject</th>
                  <th>Faculty</th>
                  <th>Room</th>
                  <th>Type</th>
                  <th>Status</th>
                  <th>Action</th>
                </tr>
              </thead>

              <tbody>
                {selectedRows.map((row) => {
                  const timing = PERIOD_TIMINGS[row.period];
                  const subjectDetails = SUBJECT_DETAILS[row.subject];

                  const isCurrentRow =
                    selectedDay === defaultDay && row.period === currentPeriod;

                  const key = `${selectedDay}-${row.period}`;
                  const isProcessing = processingKey === key;

                  return (
                    <tr
                      key={`${selectedDay}-${row.period}`}
                      className={isCurrentRow ? "active-period-row" : ""}
                    >
                      <td>
                        <strong>{row.period}</strong>
                        {isCurrentRow && (
                          <span className="recommended-mini">Now</span>
                        )}
                      </td>

                      <td>
                        {timing.start} - {timing.end}
                      </td>

                      <td>
                        <strong>{row.subject}</strong>
                        <p className="table-subtext">
                          {subjectDetails?.fullName || row.subject}
                        </p>
                      </td>

                      <td>{subjectDetails?.faculty || "-"}</td>

                      <td>{row.room}</td>

                      <td>
                        <span
                          className={`type-badge ${
                            row.type === "Lab"
                              ? "lab"
                              : row.type === "Break"
                              ? "break"
                              : "theory"
                          }`}
                        >
                          {row.type}
                        </span>
                      </td>

                      <td>{getStatusBadge(row)}</td>

                      <td>
                        {row.period === "Lunch" ? (
                          <button className="small-button ghost" disabled>
                            No Action
                          </button>
                        ) : (
                          <button
                            className={
                              isCurrentRow && recommendation.canProcess
                                ? "small-button glow"
                                : "small-button"
                            }
                            onClick={() => processAttendance(row)}
                            disabled={isProcessing}
                          >
                            {isProcessing ? "Processing..." : "Process"}
                          </button>
                        )}

                        {isCurrentRow && recommendation.canProcess && (
                          <span className="recommended-now-badge">
                            Recommended Now
                          </span>
                        )}
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

export default Timetable;