import AttendanceTable from "../components/AttendanceTable";
import { attendanceRows } from "../data/attendanceData";

function Attendance() {
  return (
    <>
      <header className="topbar">
        <div>
          <h1>Attendance</h1>
          <p>View and verify attendance marked from CCTV checkpoints.</p>
        </div>

        <button className="admin-btn">Process Current Period</button>
      </header>

      <section className="section-block">
        <div className="section-title">
          <h2>Checkpoint Summary</h2>
          <p>Present status is decided based on checkpoint recognition count.</p>
        </div>

        <div className="period-grid">
          <div className="period-card">
            <div>
              <h3>5</h3>
              <p>Total Checkpoints</p>
              <span>9:10, 9:20, 9:30, 9:40, 9:50</span>
            </div>
          </div>

          <div className="period-card">
            <div>
              <h3>3+</h3>
              <p>Present Rule</p>
              <span>Minimum checkpoints required</span>
            </div>
          </div>

          <div className="period-card">
            <div>
              <h3>10 sec</h3>
              <p>Clip Length</p>
              <span>Each checkpoint video duration</span>
            </div>
          </div>
        </div>
      </section>

      <AttendanceTable rows={attendanceRows} />
    </>
  );
}

export default Attendance;