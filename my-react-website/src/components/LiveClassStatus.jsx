import { useEffect, useState } from "react";

function LiveClassStatus({ onProcessCurrent }) {
  const [context, setContext] = useState(null);
  const [localTime, setLocalTime] = useState("");
  const [loading, setLoading] = useState(true);

  const loadContext = async () => {
    try {
      const response = await fetch("/api/current-context");
      if (response.ok) {
        const data = await response.json();
        setContext(data);
      }
    } catch (error) {
      console.error("Failed to load context:", error);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadContext();
    const interval = setInterval(loadContext, 30000); // Refresh every 30 seconds
    return () => clearInterval(interval);
  }, []);

  useEffect(() => {
    const timeInterval = setInterval(() => {
      const now = new Date();
      setLocalTime(now.toLocaleTimeString("en-US", { hour12: true }));
    }, 1000);
    return () => clearInterval(timeInterval);
  }, []);

  if (loading) {
    return (
      <div className="live-status-card">
        <p>Loading live status...</p>
      </div>
    );
  }

  if (!context) {
    return (
      <div className="live-status-card">
        <p>Unable to load live status</p>
      </div>
    );
  }

  const getStatusBadge = () => {
    switch (context.status_type) {
      case "recommended":
        return <span className="status-badge recommended">Recommended Now</span>;
      case "wait":
        return <span className="status-badge wait">Wait for Settling Time</span>;
      case "lunch":
        return <span className="status-badge lunch">Lunch Break</span>;
      default:
        return <span className="status-badge inactive">No Active Period</span>;
    }
  };

  const formatDate = (dateStr, dayName) => {
    const date = new Date(dateStr.split("-").reverse().join("-"));
    return date.toLocaleDateString("en-US", {
      weekday: "long",
      year: "numeric",
      month: "long",
      day: "numeric",
    });
  };

  return (
    <div className="live-status-card">
      <div className="live-status-header">
        <div className="live-status-title">
          <span className="clock-icon">🕐</span>
          <h3>Live Class Status</h3>
        </div>
        {getStatusBadge()}
      </div>

      <div className="live-status-content">
        <div className="live-status-time">
          <div className="live-date">
            {formatDate(context.current_date, context.current_day)}
          </div>
          <div className="live-clock">{localTime || context.display_time}</div>
        </div>

        {context.current_period && context.current_period !== "Lunch" && (
          <div className="live-period-info">
            <div className="period-detail">
              <span className="detail-label">Current Period</span>
              <span className="detail-value">{context.current_period}</span>
            </div>
            <div className="period-detail">
              <span className="detail-label">Subject</span>
              <span className="detail-value">{context.current_subject}</span>
            </div>
            <div className="period-detail">
              <span className="detail-label">Faculty</span>
              <span className="detail-value">{context.current_faculty}</span>
            </div>
            <div className="period-detail">
              <span className="detail-label">Room</span>
              <span className="detail-value">{context.current_room}</span>
            </div>
          </div>
        )}

        <div className="live-recommendation">
          <p>{context.recommendation}</p>
        </div>

        {context.attendance && Object.keys(context.attendance).length > 0 && (
          <div className="live-attendance">
            <div className="attendance-stat">
              <span className="att-label">Total Students</span>
              <span className="att-value">{context.attendance.total_students}</span>
            </div>
            <div className="attendance-stat">
              <span className="att-label">Present</span>
              <span className="att-value present">{context.attendance.present}</span>
            </div>
            <div className="attendance-stat">
              <span className="att-label">Absent</span>
              <span className="att-value absent">{context.attendance.absent}</span>
            </div>
            <div className="attendance-stat">
              <span className="att-label">Recognition Rate</span>
              <span className="att-value">{context.attendance.recognition_rate}%</span>
            </div>
          </div>
        )}

        {context.can_process && onProcessCurrent && (
          <button
            className="process-current-btn"
            onClick={() => onProcessCurrent(context)}
          >
            Process Current Period
          </button>
        )}
      </div>
    </div>
  );
}

export default LiveClassStatus;
