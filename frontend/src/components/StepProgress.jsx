export default function StepProgress({ steps, currentStep }) {
  return (
    <div className="step-progress">
      {steps.map((label, index) => {
        const isDone = index < currentStep;
        const isActive = index === currentStep;
        
        return (
          <div key={index} style={{ display: "flex", alignItems: "center" }}>
            <div className="step-item">
              <div className={`step-dot ${isActive ? "step-dot--active" : ""} ${isDone ? "step-dot--done" : ""}`}>
                {isDone ? "✓" : index + 1}
              </div>
              <span className={`step-label ${isActive ? "step-label--active" : ""} ${isDone ? "step-label--done" : ""}`}>
                {label}
              </span>
            </div>
            {index < steps.length - 1 && (
              <div className={`step-connector ${isDone ? "step-connector--done" : ""}`} />
            )}
          </div>
        );
      })}
    </div>
  );
}
