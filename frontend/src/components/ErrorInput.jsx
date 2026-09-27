/**
 * ErrorInput.jsx
 * --------------
 * Textarea for Python traceback / error input.
 * Includes chip-style demo error preset buttons and the primary Analyze action.
 */

import {
  DEMO_ERROR,
  DEMO_ERROR_NAMEERROR,
  DEMO_ERROR_INDEXERROR,
} from '../services/demo.js'

export default function ErrorInput({ error, onChange, onAnalyze, loading }) {
  return (
    <section className="panel panel--error-input" aria-labelledby="error-input-heading">
      <div className="panel-header">
        <h2 id="error-input-heading" className="panel-title">
          Traceback / Error
        </h2>
        <div className="panel-actions">
          <span className="panel-hint" style={{ marginRight: '0.1rem' }}>Try:</span>
          <button
            className="btn btn--chip"
            onClick={() => onChange(DEMO_ERROR)}
            type="button"
            title="ZeroDivisionError demo traceback"
          >
            ZeroDivision
          </button>
          <button
            className="btn btn--chip"
            onClick={() => onChange(DEMO_ERROR_NAMEERROR)}
            type="button"
            title="NameError demo traceback"
          >
            NameError
          </button>
          <button
            className="btn btn--chip"
            onClick={() => onChange(DEMO_ERROR_INDEXERROR)}
            type="button"
            title="IndexError demo traceback"
          >
            IndexError
          </button>
          <button
            className="btn btn--ghost btn--sm"
            onClick={() => onChange('')}
            type="button"
            disabled={!error}
            aria-label="Clear traceback"
          >
            Clear
          </button>
        </div>
      </div>

      <label htmlFor="error-textarea" className="sr-only">
        Python traceback or error message
      </label>
      <textarea
        id="error-textarea"
        className="code-textarea code-textarea--error"
        value={error}
        onChange={(e) => onChange(e.target.value)}
        placeholder={`Traceback (most recent call last):\n  File "script.py", line N, in func\n    ...\nExceptionType: message\n\nPaste a real traceback or click one of the demo chips above.`}
        spellCheck={false}
        autoCapitalize="off"
        autoCorrect="off"
        rows={8}
        aria-label="Python traceback or error message"
      />

      <div className="analyze-row">
        <button
          className="btn btn--primary btn--lg"
          onClick={onAnalyze}
          disabled={loading}
          type="button"
          aria-busy={loading}
        >
          {loading ? 'Analyzing…' : 'Analyze Bug'}
        </button>
        <span className="panel-hint">
          {error
            ? 'Ready — click to identify the root cause.'
            : 'Paste a traceback above first.'}
        </span>
      </div>
    </section>
  )
}
