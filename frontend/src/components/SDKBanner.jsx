export default function SDKBanner({ sdkInfo }) {
  if (!sdkInfo?.has_sdk || !sdkInfo?.sdks?.length) return null;

  return (
    <div className="sdk-banner">
      <div className="sdk-banner-icon">💡</div>
      <div className="sdk-banner-content">
        <p className="sdk-banner-title">Official SDK Available</p>
        <p className="sdk-banner-note">{sdkInfo.note}</p>
        <div className="sdk-list">
          {sdkInfo.sdks.map((sdk, i) => (
            <div key={i} className="sdk-item">
              <span className="sdk-lang">{sdk.language}</span>
              <code className="sdk-install">{sdk.install}</code>
              {sdk.docs && (
                <a href={sdk.docs} target="_blank" rel="noreferrer" className="sdk-docs">
                  Docs ↗
                </a>
              )}
            </div>
          ))}
        </div>
      </div>
      <p className="sdk-banner-sub">DevForge generated a wrapper anyway — useful for learning or customization.</p>
    </div>
  );
}
