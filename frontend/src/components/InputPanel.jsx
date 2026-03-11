import { useState } from "react";

const EXAMPLES = [
  { url: "https://stripe.com/docs/api", useCase: "Process payments and manage subscriptions" },
  { url: "https://docs.github.com/en/rest", useCase: "Manage repositories and automate CI/CD" },
  { url: "https://openweathermap.org/api", useCase: "Show real-time weather on a dashboard" },
];

export default function InputPanel({ onSubmit, loading, language, onLanguageChange, error }) {
  const [url, setUrl] = useState("");
  const [useCase, setUseCase] = useState("");

  function handleSubmit(e) {
    e.preventDefault();
    if (!url.trim() || !useCase.trim()) return;
    onSubmit({ url: url.trim(), useCase: useCase.trim() });
  }

  function loadExample(ex) {
    setUrl(ex.url);
    setUseCase(ex.useCase);
  }

  return (
    <div className="input-panel">
      <div className="input-card">
        <h2 className="card-title">Analyze an API</h2>
        <p className="card-subtitle">
          Paste any API documentation URL and describe what you want to build.
        </p>

        {error && (
          <div className="error-banner">
            <span className="error-icon">⚠️</span>
            <span>{error}</span>
          </div>
        )}

        <form onSubmit={handleSubmit} className="input-form">
          <div className="field">
            <label className="field-label">API Documentation URL</label>
            <input
              type="url"
              className="field-input"
              placeholder="https://stripe.com/docs/api"
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
              {["python", "javascript"].map((lang) => (
                <button
                  key={lang}
                  type="button"
                  className={`lang-btn ${language === lang ? "lang-btn--active" : ""}`}
                  onClick={() => onLanguageChange(lang)}
                >
                  {lang === "python" ? "🐍 Python" : "🟨 JavaScript"}
                </button>
              ))}
            </div>
          </div>

          <button
            type="submit"
            className="submit-btn"
            disabled={loading || !url || !useCase}
          >
            {loading ? "Analyzing..." : "⚡ Generate Wrapper"}
          </button>
        </form>

        <div className="examples">
          <p className="examples-label">Try an example:</p>
          <div className="examples-list">
            {EXAMPLES.map((ex, i) => (
              <button
                key={i}
                className="example-chip"
                onClick={() => loadExample(ex)}
                type="button"
              >
                {ex.url.replace("https://", "").split("/")[0]}
              </button>
            ))}
          </div>
        </div>
      </div>
    </div>
  );
}
