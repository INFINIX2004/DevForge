const API_BASE_URL = (
  import.meta.env.VITE_API_BASE_URL || "http://localhost:8000"
).replace(/\/$/, "");

async function post(path, payload) {
  const response = await fetch(`${API_BASE_URL}${path}`, {
    method: "POST",
    headers: {
      "Content-Type": "application/json"
    },
    body: JSON.stringify(payload)
  });

  const contentType = response.headers.get("content-type") || "";
  const data = contentType.includes("application/json")
    ? await response.json()
    : await response.text();

  if (!response.ok) {
    const message =
      (typeof data === "object" && (data.message || data.error)) ||
      "Request failed";

    throw new Error(message);
  }

  return data;
}

export function analyzeDocs(payload) {
  return post("/analyze", payload);
}

export function generateIntegration(payload) {
  return post("/generate", payload);
}

export function analyzeAndGenerate(payload) {
  return post("/analyze-and-generate", payload);
}
