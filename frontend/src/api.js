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

export function analyzeDocs({ url, useCase, language }) {
  return post("/analyze", {
    url,
    use_case: useCase,
    language,
  });
}

export function generateIntegration({ extracted, useCase, language }) {
  return post("/generate", {
    extracted,
    use_case: useCase,
    language,
  });
}

export function analyzeAndGenerate({ url, useCase, language }) {
  return post("/analyze-and-generate", {
    url,
    use_case: useCase,
    language,
  });
}

export function generateCode({ extracted, useCase, language }) {
  return post("/generate", {
    extracted,
    use_case: useCase,
    language,
  });
}
