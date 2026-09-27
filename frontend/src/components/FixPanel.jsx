/**
 * FixPanel.jsx
 * ------------
 * Displays the proposed fix returned by POST /fix.
 * The user must explicitly click "Apply Fix" — the code is NEVER
 * modified automatically.
 *
 * Expected `fix` shape:
 *   fix_available, explanation, proposed_change,
 *   original_code, fixed_code, diff
 */

import { useState } from 'react'

export default function FixPanel({ fix, onApplyFix }) {
  const [applied, setApplied] = useState(false)
  const [tab, setTab] = useState('diff') // 'diff' | 'original' | 'fixed'

  if (!fix) return null

  const {
    fix_available,
    explanation,
    proposed_change,
    original_code,
    fixed_code,
    diff,
  } = fix

  function handleApply() {
    if (onApplyFix) {
      onApplyFix(fixed_code)
      setApplied(true)
    }
  }

  return (
    <section className="panel panel--result" aria-labelledby="fix-heading">
      <div className="panel-header">
        <h2 id="fix-heading" className="panel-title panel-title--lg">
          Proposed Fix
        </h2>
        {fix_available ? (
          <span className="badge badge--green">Fix Available</span>
        ) : (
          <span className="badge badge--yellow">No Automatic Fix</span>
        )}
      </div>

      {!fix_available && (
        <div className="info-box info-box--warning">
          <p>No automatic fix could be generated. Review the root cause explanation above and apply a fix manually.</p>
        </div>
      )}

      {explanation && (
        <div className="fix-explanation">
          <h3 className="subsection-title">Explanation</h3>
          <p className="explanation-text">{explanation}</p>
        </div>
      )}

      {proposed_change && (
        <div className="fix-proposed-change">
          <h3 className="subsection-title">Proposed Change</h3>
          <p className="explanation-text">{proposed_change}</p>
        </div>
      )}

      {fix_available && (
        <>
          <div className="code-tabs" role="tablist" aria-label="Code view">
            {['diff', 'original', 'fixed'].map((t) => (
              <button
                key={t}
                role="tab"
                aria-selected={tab === t}
                className={`code-tab ${tab === t ? 'code-tab--active' : ''}`}
                onClick={() => setTab(t)}
                type="button"
              >
                {t === 'diff' ? 'Diff' : t === 'original' ? 'Original' : 'Fixed'}
              </button>
            ))}
          </div>

          {tab === 'diff' && (
            <pre className="code-block" aria-label="Unified diff">
              <DiffView diff={diff} />
            </pre>
          )}
          {tab === 'original' && (
            <pre className="code-block" aria-label="Original code">
              <code>{original_code}</code>
            </pre>
          )}
          {tab === 'fixed' && (
            <pre className="code-block code-block--fixed" aria-label="Fixed code">
              <code>{fixed_code}</code>
            </pre>
          )}

          <div className="panel-footer">
            {applied ? (
              <div className="applied-notice">
                <span className="badge badge--green">Fix applied to editor</span>
                <span className="panel-hint">
                  Review the updated code in the editor, then re-run analysis and tests.
                </span>
              </div>
            ) : (
              <>
                <button
                  className="btn btn--accent btn--lg"
                  onClick={handleApply}
                  type="button"
                >
                  Apply Fix to Editor
                </button>
                <span className="panel-hint">
                  Copies the fixed code into the editor — you can review before running tests.
                </span>
              </>
            )}
          </div>
        </>
      )}
    </section>
  )
}

/** Renders a unified diff with +/- line colouring */
function DiffView({ diff }) {
  if (!diff) return <code>No diff available.</code>
  return (
    <>
      {diff.split('\n').map((line, i) => {
        let cls = ''
        if (line.startsWith('+') && !line.startsWith('+++')) cls = 'diff-add'
        else if (line.startsWith('-') && !line.startsWith('---')) cls = 'diff-remove'
        else if (line.startsWith('@@')) cls = 'diff-hunk'
        return (
          <span key={i} className={cls}>
            {line}
            {'\n'}
          </span>
        )
      })}
    </>
  )
}
