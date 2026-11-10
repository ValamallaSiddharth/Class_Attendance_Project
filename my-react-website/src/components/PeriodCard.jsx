function PeriodCard({ period, subject, time, status }) {
  return (
    <div className="period-card">
      <div>
        <h3>{period}</h3>
        <p>{subject}</p>
        <span>{time}</span>
      </div>

      <button className={`period-btn ${status.toLowerCase()}`}>
        {status}
      </button>
    </div>
  );
}

export default PeriodCard;
