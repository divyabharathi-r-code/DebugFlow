/**
 * AnalysisPanel.jsx
 * -----------------
 * Displays the structured root-cause analysis returned by POST /analyze.
 *
 * Expected `analysis` shape (from response.root_cause):
 *   error_type, error_message, affected_function, affected_line,
 *   root_cause, explanation, confidence
 */

export default function AnalysisPanel({ analysis, onRequestFix, fixLoading }) {
  if (!analysis) return null

  const {
    error_type,
    error_message,
    affected_function,
    affected_line,
    root_cause,
    explanation,
    confidence,
  } = analysis

  const confidencePct = Math.round((confidence ?? 0) * 100)
  const confidenceClass =
    confidencePct >= 85
      ? 'confidence--high'
      : confidencePct >= 60
      ? 'confidence--medium'
      : 'confidence--low'

  return (
    <section className="panel panel--result" aria-labelledby="analysis-heading">
      <div className="panel-header">
        <h2 id="analysis-heading" className="panel-title panel-title--lg">
          Root Cause Analysis
        </h2>
        <span className={`confidence-badge ${confidenceClass}`}>
          {confidencePct}% confidence
        </span>
      </div>

      <div className="analysis-grid">
        <Field label="Error Type"        value={error_type} mono />
        <Field label="Error Message"     value={error_message} mono />
        <Field label="Affected Function" value={affected_function || '—'} mono />
        <Field label="Affected Line"     value={affected_line != null ? `Line ${affected_line}` : '—'} />
        <Field label="Root Cause"        value={root_cause} className="field--highlight" />
        <Field label="Explanation"       value={explanation} wide />
      </div>

      <div className="panel-footer">
        <button
          className="btn btn--primary btn--lg"
          onClick={onRequestFix}
          disabled={fixLoading}
          type="button"
          aria-busy={fixLoading}
        >
          {fixLoading ? 'Generating Fix…' : 'Generate Fix'}
        </button>
        <span className="panel-hint">
          Uses the root cause above to produce a targeted code fix.
        </span>
      </div>
    </section>
  )
}

function Field({ label, value, mono, wide, className }) {
  return (
    <div className={`analysis-field ${wide ? 'analysis-field--wide' : ''} ${className || ''}`}>
      <dt className="field-label">{label}</dt>
      <dd className={`field-value ${mono ? 'field-value--mono' : ''}`}>{value}</dd>
    </div>
  )
}
