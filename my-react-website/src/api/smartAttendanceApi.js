const API_BASE_URL = "";

async function requestJson(url, options = {}) {
  try {
    const response = await fetch(`${API_BASE_URL}${url}`, {
      headers: {
        "Content-Type": "application/json",
        ...(options.headers || {}),
      },
      ...options,
    });

    const data = await response.json().catch(() => ({}));

    if (!response.ok) {
      throw new Error(
        data.error ||
          data.stderr ||
          data.message ||
          `Request failed with status ${response.status}`
      );
    }

    return data;
  } catch (error) {
    console.error(`API request failed: ${url}`, error);
    throw error;
  }
}

export async function getHealth() {
  return requestJson("/api/health");
}

export async function getDashboardData() {
  return requestJson("/api/dashboard");
}

export async function getCurrentContext() {
  return requestJson("/api/current-context");
}

export async function getLatestAttendance() {
  return requestJson("/api/attendance/latest");
}

export async function getReports() {
  return requestJson("/api/reports");
}

export async function getJobs() {
  return requestJson("/api/jobs");
}

export async function getVideos() {
  return requestJson("/api/videos");
}

export async function processPeriod({ day, period, time }) {
  return requestJson("/api/process-period", {
    method: "POST",
    body: JSON.stringify({
      day,
      period,
      time,
    }),
  });
}

export async function reprocessPeriod({ day, period, time }) {
  return requestJson("/api/reprocess-period", {
    method: "POST",
    body: JSON.stringify({
      day,
      period,
      time,
    }),
  });
}

export async function saveManualEdit({ source_file, rows }) {
  return requestJson("/api/manual-edit", {
    method: "POST",
    body: JSON.stringify({
      source_file,
      rows,
    }),
  });
}