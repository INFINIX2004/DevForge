import { useState } from "react";

export default function CodeOutput({ code }) {
  const [activeTab, setActiveTab] = useState("wrapper");
  const [copied, setCopied] = useState(false);

  const currentCode = activeTab === "wrapper" ? code.wrapper_class : code.usage_example;

  async function handleCopy() {
    await navigator.clipboard.writeText(currentCode);
    setCopied(true);
    setTimeout(() => setCopied(false), 2000);
  }

  async function handleCopyAll() {
    const full = `${code.wrapper_class}\n\n${code.usage_example}`;
    await navigator.clipboard.writeText(full);
    setCopied(true);
    setTimeout(() => setCopied(false), 2000);
  }

  const langLabel = code.language === "python" ? "Python" : "JavaScript";
  const langIcon = code.language === "python" ? "🐍" : "🟨";

  return (
    <div className="panel code-panel">
      <div className="code-panel-header">
        <h3 className="panel-title">
          {langIcon} Generated {langLabel} Wrapper
        </h3>
        <div className="code-actions">
          <button className="copy-btn" onClick={handleCopyAll}>
            {copied ? "✓ Copied!" : "Copy All"}
          </button>
        </div>
      </div>

      {/* Tabs */}
      <div className="code-tabs">
        <button
          className={`code-tab ${activeTab === "wrapper" ? "code-tab--active" : ""}`}
          onClick={() => setActiveTab("wrapper")}
        >
          Wrapper Class
        </button>
        <button
          className={`code-tab ${activeTab === "example" ? "code-tab--active" : ""}`}
          onClick={() => setActiveTab("example")}
        >
          Usage Example
        </button>
      </div>

      {/* Code block */}
      <div className="code-block-wrapper">
        <button className="copy-inline-btn" onClick={handleCopy}>
          {copied ? "✓" : "Copy"}
        </button>
        <pre className="code-block">
          <code>{currentCode}</code>
        </pre>
      </div>
    </div>
  );
}
