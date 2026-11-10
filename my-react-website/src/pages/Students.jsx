function Students() {
  return (
    <>
      <header className="topbar">
        <div>
          <h1>Students</h1>
          <p>Manage registered students and dataset status.</p>
        </div>

        <button className="admin-btn">Add Student</button>
      </header>

      <section className="table-card">
        <div className="table-header">
          <h2>Student Dataset</h2>
          <button>Export List</button>
        </div>

        <table>
          <thead>
            <tr>
              <th>Roll No</th>
              <th>Name</th>
              <th>Image Count</th>
              <th>Dataset Status</th>
            </tr>
          </thead>

          <tbody>
            <tr>
              <td>24011CSEAI0101</td>
              <td>Student 1</td>
              <td>20</td>
              <td>
                <span className="status present">Good</span>
              </td>
            </tr>

            <tr>
              <td>24011CSEAI0102</td>
              <td>Student 2</td>
              <td>14</td>
              <td>
                <span className="status absent">Needs Update</span>
              </td>
            </tr>

            <tr>
              <td>24011CSEAI0103</td>
              <td>V Siddharth</td>
              <td>22</td>
              <td>
                <span className="status present">Good</span>
              </td>
            </tr>
          </tbody>
        </table>
      </section>
    </>
  );
}

export default Students;