import { useState } from "react";

const LANGUAGES = [
  { id: "python",     label: "Python",     icon: "🐍" },
  { id: "javascript", label: "JS",         icon: "🟨" },
  { id: "typescript", label: "TS",         icon: "🔷" },
  { id: "curl",       label: "curl",       icon: "⚡" },
];

export default function CodeOutput({ code, language, onLanguageChange }) {
  const [activeTab, setActiveTab] = useState("wrapper");
  const [copied, setCopied] = useState(false);

  const currentCode = activeTab === "wrapper" ? code.wrapper_class : code.usage_example;

  async function handleCopy() {
    const full = `${code.wrapper_class}\n\n${code.usage_example}`;
    await navigator.clipboard.writeText(full);
    setCopied(true);
    setTimeout(() => setCopied(false), 2000);
  }

  return (
    <div className="panel code-panel">
      <div className="code-panel-header">
        <h3 className="panel-title">Generated Wrapper</h3>
        <button className="copy-btn" onClick={handleCopy}>
          {copied ? "✓ Copied!" : "Copy All"}
        </button>
      </div>

      {/* Language switcher */}
      <div className="lang-switcher">
        {LANGUAGES.map((lang) => (
          <button
            key={lang.id}
            className={`lang-switch-btn ${language === lang.id ? "lang-switch-btn--active" : ""}`}
            onClick={() => onLanguageChange(lang.id)}
          >
            {lang.icon} {lang.label}
          </button>
        ))}
      </div>

      {/* Tabs */}
      <div className="code-tabs">
        <button className={`code-tab ${activeTab === "wrapper" ? "code-tab--active" : ""}`}
          onClick={() => setActiveTab("wrapper")}>
          {code.language === "curl" ? "Commands" : "Wrapper Class"}
        </button>
        <button className={`code-tab ${activeTab === "example" ? "code-tab--active" : ""}`}
          onClick={() => setActiveTab("example")}>
          Usage Example
        </button>
      </div>

      <div className="code-block-wrapper">
        <button className="copy-inline-btn" onClick={async () => {
          await navigator.clipboard.writeText(currentCode);
          setCopied(true);
          setTimeout(() => setCopied(false), 2000);
        }}>{copied ? "✓" : "Copy"}</button>
        <pre className="code-block"><code>{currentCode}</code></pre>
      </div>
    </div>
  );
}
