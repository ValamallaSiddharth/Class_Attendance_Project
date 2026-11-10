import { useEffect, useState } from "react";
import { getReports } from "../api/smartAttendanceApi";

function Reports() {
  const [reports, setReports] = useState([]);
  const [loading, setLoading] = useState(true);

  const loadReports = async () => {
    try {
      setLoading(true);
      const data = await getReports();
      setReports(data);
    } catch (error) {
      console.error("Failed to load reports:", error);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadReports();
  }, []);

  const getFileTypeBadge = (type) => {
    switch (type) {
      case "csv":
        return <span className="file-type-badge csv">CSV</span>;
      case "xlsx":
        return <span className="file-type-badge xlsx">XLSX</span>;
      case "pdf":
        return <span className="file-type-badge pdf">PDF</span>;
      case "html":
        return <span className="file-type-badge html">HTML</span>;
      default:
        return <span className="file-type-badge">{type.toUpperCase()}</span>;
    }
  };

  return (
    <>
      <header className="topbar">
        <div>
          <h1>Attendance Reports</h1>
          <p>Download attendance reports, logs, and summaries.</p>
        </div>

        <button className="admin-btn" onClick={loadReports}>
          Refresh Reports
        </button>
      </header>

      {loading ? (
        <section className="section-block">
          <p>Loading reports...</p>
        </section>
      ) : (
        <section className="section-block">
          <div className="section-title">
            <h2>Available Reports</h2>
            <p>
              {reports.length} file{reports.length !== 1 ? "s" : ""} in exports/
              folder
            </p>
          </div>

          {reports.length === 0 ? (
            <div className="empty-state">
              <div className="empty-state-icon">📄</div>
              <h3>No Reports Found</h3>
              <p>Process a period to generate attendance reports.</p>
            </div>
          ) : (
            <div className="table-card">
              <table>
                <thead>
                  <tr>
                    <th>Type</th>
                    <th>Filename</th>
                    <th>Size</th>
                    <th>Actions</th>
                  </tr>
                </thead>
                <tbody>
                  {reports.map((report) => (
                    <tr key={report.name}>
                      <td>{getFileTypeBadge(report.type)}</td>
                      <td>
                        <strong>{report.name}</strong>
                      </td>
                      <td>{report.size_kb} KB</td>
                      <td>
                        <div className="action-group">
                          <a
                            href={report.download_url}
                            download
                            style={{ textDecoration: "none" }}
                          >
                            <button className="mini-btn">Download</button>
                          </a>
                          <a
                            href={report.download_url}
                            target="_blank"
                            rel="noopener noreferrer"
                            style={{ textDecoration: "none" }}
                          >
                            <button className="mini-btn">Open</button>
                          </a>
                        </div>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          )}
        </section>
      )}
    </>
  );
}

export default Reports;