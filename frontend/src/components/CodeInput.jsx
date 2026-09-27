/**
 * CodeInput.jsx
 * -------------
 * Large textarea for Python source code input.
 * Includes Load Demo and Clear actions.
 */

import { DEMO_CODE } from '../services/demo.js'

export default function CodeInput({ code, onChange }) {
  const lineCount = code ? code.split('\n').length : 0
  const charCount = code ? code.length : 0

  return (
    <section className="panel panel--code-input" aria-labelledby="code-input-heading">
      <div className="panel-header">
        <h2 id="code-input-heading" className="panel-title">
          Python Source Code
        </h2>
        <div className="panel-actions">
          <button
            className="btn btn--secondary btn--sm"
            onClick={() => onChange(DEMO_CODE)}
            type="button"
            title="Load the example buggy Python script"
          >
            Load Demo
          </button>
          <button
            className="btn btn--ghost btn--sm"
            onClick={() => onChange('')}
            type="button"
            disabled={!code}
          >
            Clear
          </button>
        </div>
      </div>

      <label htmlFor="code-editor" className="sr-only">
        Python source code
      </label>
      <textarea
        id="code-editor"
        className="code-textarea"
        value={code}
        onChange={(e) => onChange(e.target.value)}
        placeholder="# Paste your Python source code here…&#10;# Or click Load Demo to use the sample buggy script."
        spellCheck={false}
        autoCapitalize="off"
        autoCorrect="off"
        rows={18}
        aria-label="Python source code editor"
      />
      <div className="textarea-meta">
        <p className="panel-hint">
          {code
            ? `${lineCount} line${lineCount !== 1 ? 's' : ''} · ${charCount} chars`
            : 'Paste code above, or use Load Demo for a ready-made example.'}
        </p>
      </div>
    </section>
  )
}
