/**
 * Header.jsx
 * ----------
 * Top application header with CSS-only logo mark and backend status pill.
 * The logo uses a </> code-bracket motif with a red breakpoint dot (pure CSS).
 */

export default function Header({ backendStatus }) {
  return (
    <header className="app-header">
      <div className="header-brand">
        <div className="header-logo-wrap" aria-hidden="true">
          <span className="header-logo-mark">&lt;/&gt;</span>
        </div>
        <div className="header-text">
          <h1 className="header-title">DebugFlow</h1>
          <p className="header-tagline">Understand · Fix · Verify</p>
        </div>
      </div>
      <div className={`backend-status backend-status--${backendStatus}`}>
        <span className="status-dot" aria-hidden="true" />
        {backendStatus === 'online'   && 'Backend online'}
        {backendStatus === 'offline'  && 'Backend offline'}
        {backendStatus === 'checking' && 'Checking…'}
      </div>
    </header>
  )
}
