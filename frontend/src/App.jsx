import { useState } from "react";
import InputPanel from "./components/InputPanel";
import StepProgress from "./components/StepProgress";
import EndpointViewer from "./components/EndpointViewer";
import CodeOutput from "./components/CodeOutput";
import { analyzeAndGenerate } from "./api";

const STEPS = ["Input", "Scraping", "Extracting", "Generating", "Done"];

export default function App() {
  const [step, setStep] = useState(0);       // 0 = idle
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);
  const [result, setResult] = useState(null);  // { extracted, code, pages_scraped }
  const [language, setLanguage] = useState("python");

  async function handleSubmit({ url, useCase }) {
    setLoading(true);
    setError(null);
    setResult(null);
    setStep(1);

    try {
      // Simulate step progression for UX
      setTimeout(() => setStep(2), 1500);
      setTimeout(() => setStep(3), 3500);

      const data = await analyzeAndGenerate({ url, useCase, language });

      if (!data.success) {
        throw new Error(data.error || "Unknown error occurred");
      }

      setStep(4);
      setResult(data);
    } catch (err) {
      setError(err.message);
      setStep(0);
    } finally {
      setLoading(false);
    }
  }

  function handleReset() {
    setStep(0);
    setResult(null);
    setError(null);
    setLoading(false);
  }

  return (
    <div className="app">
      <header className="app-header">
        <div className="logo">
          <span className="logo-icon">⚡</span>
          <span className="logo-text">DevForge</span>
        </div>
        <p className="tagline">Paste an API docs URL. Get a working wrapper in seconds.</p>
      </header>

      <main className="app-main">
        {/* Step progress bar */}
        {step > 0 && (
          <StepProgress steps={STEPS} currentStep={step} />
        )}

        {/* Input form — always shown unless loading or done */}
        {(step === 0 || error) && (
          <InputPanel
            onSubmit={handleSubmit}
            loading={loading}
            language={language}
            onLanguageChange={setLanguage}
            error={error}
          />
        )}

        {/* Loading state */}
        {loading && (
          <div className="loading-state">
            <div className="spinner" />
            <p className="loading-text">{STEPS[step]}...</p>
          </div>
        )}

        {/* Results */}
        {result && !loading && (
          <div className="results">
            <div className="results-header">
              <div className="results-meta">
                <h2 className="api-name">{result.extracted.api_name}</h2>
                <p className="api-summary">{result.extracted.raw_summary}</p>
                <span className="pages-badge">
                  📄 {result.pages_scraped} page{result.pages_scraped !== 1 ? "s" : ""} scraped
                </span>
              </div>
              <button className="reset-btn" onClick={handleReset}>
                ← New API
              </button>
            </div>

            <div className="results-grid">
              <EndpointViewer extracted={result.extracted} />
              <CodeOutput code={result.code} />
            </div>
          </div>
        )}
      </main>
    </div>
  );
}
