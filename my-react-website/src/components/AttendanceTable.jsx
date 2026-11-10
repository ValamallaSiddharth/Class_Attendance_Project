function AttendanceTable({ rows }) {
  if (!rows || rows.length === 0) {
    return (
      <div className="table-card">
        <div className="table-header">
          <h2>Latest Attendance</h2>
        </div>
        <p>No attendance data found yet.</p>
      </div>
    );
  }

  const columns = Object.keys(rows[0]);

  return (
    <div className="table-card">
      <div className="table-header">
        <h2>Latest Attendance</h2>
        <button>Export Excel</button>
      </div>

      <div className="table-scroll">
        <table>
          <thead>
            <tr>
              {columns.map((column) => (
                <th key={column}>{column}</th>
              ))}
            </tr>
          </thead>

          <tbody>
            {rows.map((student, index) => (
              <tr key={index}>
                {columns.map((column) => (
                  <td key={column}>{student[column]}</td>
                ))}
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  );
}

export default AttendanceTable;
