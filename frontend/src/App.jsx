import { useState } from "react";
import InputPanel from "./components/InputPanel";
import StepProgress from "./components/StepProgress";
import EndpointViewer from "./components/EndpointViewer";
import CodeOutput from "./components/CodeOutput";
import SDKBanner from "./components/SDKBanner";
import { analyzeAndGenerate } from "./api";

const STEPS = ["Input", "Scraping", "Extracting", "Generating", "Done"];

export default function App() {
  const [step, setStep] = useState(0);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);
  const [result, setResult] = useState(null);
  const [language, setLanguage] = useState("python");

  async function handleSubmit({ url, useCase }) {
    setLoading(true);
    setError(null);
    setResult(null);
    setStep(1);

    try {
      setTimeout(() => setStep(2), 1200);
      setTimeout(() => setStep(3), 3000);
      const data = await analyzeAndGenerate({ url, useCase, language });
      if (!data.success) throw new Error(data.error || "Unknown error");
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
    setStep(0); setResult(null); setError(null); setLoading(false);
  }

  async function handleRegenerate(newLanguage) {
    if (!result) return;
    setLanguage(newLanguage);
    setLoading(true);
    try {
      const data = await analyzeAndGenerate({
        url: result.extracted.base_url,
        useCase: result.extracted.raw_summary,
        language: newLanguage,
      });
      if (data.success) setResult({ ...result, code: data.code });
    } catch (e) {
      setError(e.message);
    } finally {
      setLoading(false);
    }
  }

  return (
    <div className="app">
      <header className="app-header">
        <div className="logo">
          <span className="logo-icon">⚡</span>
          <span className="logo-text">DevForge</span>
        </div>
        <p className="tagline">Paste any API docs URL. Get a production wrapper in seconds.</p>
      </header>

      <main className="app-main">
        {step > 0 && <StepProgress steps={STEPS} currentStep={step} />}

        {(step === 0 || error) && (
          <InputPanel
            onSubmit={handleSubmit}
            loading={loading}
            language={language}
            onLanguageChange={setLanguage}
            error={error}
          />
        )}

        {loading && (
          <div className="loading-state">
            <div className="spinner" />
            <p className="loading-text">{STEPS[step] || "Processing"}...</p>
          </div>
        )}

        {result && !loading && (
          <div className="results">
            <div className="results-header">
              <div className="results-meta">
                <div className="results-title-row">
                  <h2 className="api-name">{result.extracted.api_name}</h2>
                  {result.source === "openapi" && (
                    <span className="source-badge source-badge--openapi">📋 OpenAPI</span>
                  )}
                  {result.source === "llm" && (
                    <span className="source-badge source-badge--llm">🧠 LLM Extracted</span>
                  )}
                </div>
                <p className="api-summary">{result.extracted.raw_summary}</p>
                {result.pages_scraped > 0 && (
                  <span className="pages-badge">📄 {result.pages_scraped} page(s) scraped</span>
                )}
              </div>
              <button className="reset-btn" onClick={handleReset}>← New API</button>
            </div>

            {result.extracted.sdk_info?.has_sdk && (
              <SDKBanner sdkInfo={result.extracted.sdk_info} />
            )}

            <div className="results-grid">
              <EndpointViewer extracted={result.extracted} />
              <CodeOutput
                code={result.code}
                language={language}
                onLanguageChange={handleRegenerate}
              />
            </div>
          </div>
        )}
      </main>
    </div>
  );
}
