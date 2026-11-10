import { useEffect, useState } from "react";

function ProcessingJobs() {
  const [jobs, setJobs] = useState([]);
  const [loading, setLoading] = useState(true);

  const loadJobs = async () => {
    try {
      setLoading(true);

      const response = await fetch("/api/jobs");

      if (!response.ok) {
        setJobs([]);
        return;
      }

      const data = await response.json();
      setJobs(Array.isArray(data) ? data : []);
    } catch (error) {
      console.error("Failed to load jobs:", error);
      setJobs([]);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadJobs();
  }, []);

  return (
    <div className="page">
      <div className="page-header">
        <div>
          <p className="page-kicker">PROCESSING ACTIVITY</p>
          <h1>Processing Jobs</h1>
          <p>
            Track attendance processing jobs, generated reports, and backend
            execution details.
          </p>
        </div>

        <button className="primary-button" onClick={loadJobs}>
          Refresh Jobs
        </button>
      </div>

      <div className="info-grid">
        <div className="info-card">
          <span>⚡</span>
          <div>
            <h3>{jobs.length}</h3>
            <p>Total Jobs</p>
          </div>
        </div>

        <div className="info-card">
          <span>✅</span>
          <div>
            <h3>{jobs.filter((job) => job.status === "success").length}</h3>
            <p>Successful</p>
          </div>
        </div>

        <div className="info-card">
          <span>❌</span>
          <div>
            <h3>{jobs.filter((job) => job.status === "failed").length}</h3>
            <p>Failed</p>
          </div>
        </div>
      </div>

      <div className="content-card">
        <div className="section-title-row">
          <div>
            <h2>Job History</h2>
            <p>Recent attendance processing activity from the backend.</p>
          </div>
        </div>

        {loading ? (
          <div className="empty-state">
            <div className="empty-icon">⏳</div>
            <h3>Loading jobs...</h3>
            <p>Please wait while the system loads processing history.</p>
          </div>
        ) : jobs.length === 0 ? (
          <div className="empty-state">
            <div className="empty-icon">⚡</div>
            <h3>No processing jobs yet</h3>
            <p>
              Process attendance from the Timetable Control page. Jobs will
              appear here automatically.
            </p>
          </div>
        ) : (
          <div className="jobs-list">
            {jobs.map((job, index) => (
              <div className="job-card" key={job.id || index}>
                <div className="job-main">
                  <div className="job-icon">
                    {job.status === "success" ? "✅" : "❌"}
                  </div>

                  <div>
                    <h3>
                      {job.day || "Day"} {job.period || "Period"}
                    </h3>
                    <p>
                      Started: {job.started_at || "Not available"} · Finished:{" "}
                      {job.finished_at || "Not available"}
                    </p>
                  </div>
                </div>

                <div className="job-meta">
                  <span
                    className={`status-badge ${
                      job.status === "success" ? "success" : "danger"
                    }`}
                  >
                    {job.status || "unknown"}
                  </span>

                  {job.latest_file && (
                    <a
                      className="small-link"
                      href={`/api/download/${job.latest_file}`}
                      target="_blank"
                      rel="noreferrer"
                    >
                      Open Report
                    </a>
                  )}
                </div>

                {(job.stdout || job.stderr) && (
                  <details className="job-details">
                    <summary>View backend output</summary>

                    {job.stdout && (
                      <>
                        <h4>stdout</h4>
                        <pre>{job.stdout}</pre>
                      </>
                    )}

                    {job.stderr && (
                      <>
                        <h4>stderr</h4>
                        <pre>{job.stderr}</pre>
                      </>
                    )}
                  </details>
                )}
              </div>
            ))}
          </div>
        )}
      </div>
    </div>
  );
}

export default ProcessingJobs;