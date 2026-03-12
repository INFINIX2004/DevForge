import { useState } from "react";

const EXAMPLES = [
  { url: "https://petstore3.swagger.io/api/v3/openapi.json", useCase: "Manage a pet store inventory" },
  { url: "https://docs.github.com/en/rest", useCase: "Manage repositories and automate CI/CD" },
  { url: "https://openweathermap.org/api", useCase: "Show real-time weather on a dashboard" },
];

const LANGUAGES = [
  { id: "python",     label: "Python",     icon: "🐍" },
  { id: "javascript", label: "JavaScript", icon: "🟨" },
  { id: "typescript", label: "TypeScript", icon: "🔷" },
  { id: "curl",       label: "curl",       icon: "⚡" },
];

export default function InputPanel({ onSubmit, loading, language, onLanguageChange, error }) {
  const [url, setUrl] = useState("");
  const [useCase, setUseCase] = useState("");

  function handleSubmit(e) {
    e.preventDefault();
    if (!url.trim() || !useCase.trim()) return;
    onSubmit({ url: url.trim(), useCase: useCase.trim() });
  }

  return (
    <div className="input-panel">
      <div className="input-card">
        <h2 className="card-title">Analyze an API</h2>
        <p className="card-subtitle">
          Paste any API docs URL or a <code>swagger.json</code> / <code>openapi.yaml</code> link.
        </p>

        {error && (
          <div className="error-banner">
            <span>⚠️</span>
            <span>{error}</span>
          </div>
        )}

        <form onSubmit={handleSubmit} className="input-form">
          <div className="field">
            <label className="field-label">API Documentation URL</label>
            <input
              type="url"
              className="field-input"
              placeholder="https://petstore3.swagger.io/api/v3/openapi.json"
              value={url}
              onChange={(e) => setUrl(e.target.value)}
              required
            />
          </div>

          <div className="field">
            <label className="field-label">What do you want to build?</label>
            <textarea
              className="field-input field-textarea"
              placeholder="e.g. A payment system that charges users monthly and handles refunds"
              value={useCase}
              onChange={(e) => setUseCase(e.target.value)}
              rows={3}
              required
            />
          </div>

          <div className="field">
            <label className="field-label">Output Language</label>
            <div className="lang-toggle">
              {LANGUAGES.map((lang) => (
                <button
                  key={lang.id}
                  type="button"
                  className={`lang-btn ${language === lang.id ? "lang-btn--active" : ""}`}
                  onClick={() => onLanguageChange(lang.id)}
                >
                  {lang.icon} {lang.label}
                </button>
              ))}
            </div>
          </div>

          <button type="submit" className="submit-btn" disabled={loading || !url || !useCase}>
            {loading ? "Analyzing..." : "⚡ Generate Wrapper"}
          </button>
        </form>

        <div className="examples">
          <p className="examples-label">Try an example:</p>
          <div className="examples-list">
            {EXAMPLES.map((ex, i) => (
              <button key={i} className="example-chip" type="button"
                onClick={() => { setUrl(ex.url); setUseCase(ex.useCase); }}>
                {ex.url.replace("https://", "").split("/")[0]}
              </button>
            ))}
          </div>
        </div>
      </div>
    </div>
  );
}
