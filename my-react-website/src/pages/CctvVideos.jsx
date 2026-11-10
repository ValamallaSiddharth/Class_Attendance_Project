import { useEffect, useState } from "react";

function CctvVideos() {
  const [videos, setVideos] = useState([]);
  const [loading, setLoading] = useState(true);

  const loadVideos = async () => {
    try {
      setLoading(true);

      const response = await fetch("/api/videos");

      if (!response.ok) {
        setVideos([]);
        return;
      }

      const data = await response.json();
      setVideos(Array.isArray(data) ? data : []);
    } catch (error) {
      console.error("Failed to load videos:", error);
      setVideos([]);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadVideos();
  }, []);

  return (
    <div className="page">
      <div className="page-header">
        <div>
          <p className="page-kicker">CCTV INPUT CONTROL</p>
          <h1>CCTV Videos</h1>
          <p>
            Manage classroom CCTV clips and assign them to timetable periods for
            attendance processing.
          </p>
        </div>

        <button className="primary-button" onClick={loadVideos}>
          Refresh Videos
        </button>
      </div>

      <div className="info-grid">
        <div className="info-card">
          <span>🎥</span>
          <div>
            <h3>{videos.length}</h3>
            <p>Videos Found</p>
          </div>
        </div>

        <div className="info-card">
          <span>🏫</span>
          <div>
            <h3>1106</h3>
            <p>Theory Room</p>
          </div>
        </div>

        <div className="info-card">
          <span>🧪</span>
          <div>
            <h3>1016</h3>
            <p>Lab Room</p>
          </div>
        </div>
      </div>

      <div className="content-card">
        <div className="section-title-row">
          <div>
            <h2>Available CCTV Files</h2>
            <p>Videos are loaded from backend video folders.</p>
          </div>
        </div>

        {loading ? (
          <div className="empty-state">
            <div className="empty-icon">⏳</div>
            <h3>Loading videos...</h3>
            <p>Please wait while the system checks available CCTV files.</p>
          </div>
        ) : videos.length === 0 ? (
          <div className="empty-state">
            <div className="empty-icon">🎥</div>
            <h3>No CCTV videos found yet</h3>
            <p>
              Add videos inside folders like <strong>cctv_videos</strong>,{" "}
              <strong>videos</strong>, or <strong>test_videos</strong>.
            </p>
          </div>
        ) : (
          <div className="video-grid">
            {videos.map((video, index) => (
              <div className="video-card" key={index}>
                <div className="video-thumb">🎥</div>

                <div className="video-info">
                  <h3>{video.name || video.filename || `Video ${index + 1}`}</h3>
                  <p>{video.path || "CCTV classroom video"}</p>
                </div>

                <div className="assign-row">
                  <select defaultValue="">
                    <option value="" disabled>
                      Select Day
                    </option>
                    <option>Monday</option>
                    <option>Tuesday</option>
                    <option>Wednesday</option>
                    <option>Thursday</option>
                    <option>Friday</option>
                  </select>

                  <select defaultValue="">
                    <option value="" disabled>
                      Select Period
                    </option>
                    <option>P1</option>
                    <option>P2</option>
                    <option>P3</option>
                    <option>P4</option>
                    <option>P6</option>
                    <option>P7</option>
                    <option>P8</option>
                  </select>
                </div>

                <button className="secondary-button">Assign Video</button>
              </div>
            ))}
          </div>
        )}
      </div>
    </div>
  );
}

export default CctvVideos;