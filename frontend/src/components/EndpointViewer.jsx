import { useState } from "react";

const METHOD_COLORS = {
  GET: "#22c55e",
  POST: "#3b82f6",
  PUT: "#f59e0b",
  DELETE: "#ef4444",
  PATCH: "#a855f7",
};

export default function EndpointViewer({ extracted }) {
  const [expanded, setExpanded] = useState(null);

  const { auth, endpoints, base_url } = extracted;

  return (
    <div className="panel endpoint-panel">
      <h3 className="panel-title">📡 Extracted API Info</h3>

      {/* Auth info */}
      <div className="auth-badge">
        <span className="auth-label">Auth:</span>
        <span className="auth-type">{auth.type.toUpperCase()}</span>
        {auth.header && <span className="auth-header">→ {auth.header}</span>}
        <p className="auth-desc">{auth.description}</p>
      </div>

      {/* Base URL */}
      <div className="base-url">
        <span className="base-url-label">Base URL:</span>
        <code className="base-url-value">{base_url}</code>
      </div>

      {/* Endpoints list */}
      <div className="endpoints-list">
        <p className="endpoints-count">{endpoints.length} endpoints found</p>

        {endpoints.map((ep, i) => (
          <div
            key={i}
            className={`endpoint-item ${expanded === i ? "endpoint-item--expanded" : ""}`}
          >
            <button
              className="endpoint-header"
              onClick={() => setExpanded(expanded === i ? null : i)}
            >
              <span
                className="method-badge"
                style={{ backgroundColor: METHOD_COLORS[ep.method] || "#64748b" }}
              >
                {ep.method}
              </span>
              <code className="endpoint-path">{ep.path}</code>
              <span className="endpoint-desc-short">{ep.description}</span>
              <span className="expand-icon">{expanded === i ? "▲" : "▼"}</span>
            </button>

            {expanded === i && (
              <div className="endpoint-details">
                <p className="endpoint-full-desc">{ep.description}</p>
                {ep.params.length > 0 && (
                  <div className="params-table">
                    <p className="params-title">Parameters:</p>
                    {ep.params.map((p, j) => (
                      <div key={j} className="param-row">
                        <code className="param-name">{p.name}</code>
                        <span className="param-type">{p.type}</span>
                        <span className={`param-required ${p.required ? "param-required--yes" : ""}`}>
                          {p.required ? "required" : "optional"}
                        </span>
                        <span className="param-desc">{p.description}</span>
                      </div>
                    ))}
                  </div>
                )}
              </div>
            )}
          </div>
        ))}
      </div>
    </div>
  );
}
