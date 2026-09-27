/**
 * TestResults.jsx
 * ---------------
 * Displays the test runner results from POST /run-tests.
 * Also contains the "Run Tests" button and test-code textarea.
 * Styled as the final verification stage of the debug pipeline.
 *
 * Expected `results` shape:
 *   status, passed, timed_out, returncode,
 *   stdout, stderr, tests_total, tests_passed,
 *   tests_failed, tests_errors, summary
 */

import { useState } from 'react'
import { DEMO_TEST_CODE } from '../services/demo.js'

export default function TestResults({ results, onRunTests, loading }) {
  const [testCode, setTestCode] = useState('')
  const [showOutput, setShowOutput] = useState(false)

  function handleLoad() {
    setTestCode(DEMO_TEST_CODE)
  }

  function handleRun() {
    if (onRunTests) onRunTests(testCode)
  }

  return (
    <section className="panel panel--verify" aria-labelledby="tests-heading">
      <div className="panel-header">
        <h2 id="tests-heading" className="panel-title panel-title--lg">Test Runner</h2>
        <span className="panel-hint">Final verification stage</span>
      </div>

      {/* Test code editor */}
      <div className="panel-subheader">
        <span className="panel-hint">Pytest-compatible test code:</span>
        <div className="panel-actions">
          <button
            className="btn btn--secondary btn--sm"
            onClick={handleLoad}
            type="button"
          >
            Load Demo Tests
          </button>
          <button
            className="btn btn--ghost btn--sm"
            onClick={() => setTestCode('')}
            type="button"
            disabled={!testCode}
          >
            Clear
          </button>
        </div>
      </div>

      <label htmlFor="test-code-editor" className="sr-only">
        Pytest test code
      </label>
      <textarea
        id="test-code-editor"
        className="code-textarea"
        value={testCode}
        onChange={(e) => setTestCode(e.target.value)}
        placeholder="# Paste pytest test code here…&#10;# Or click Load Demo Tests to use the sample test suite."
        spellCheck={false}
        autoCapitalize="off"
        autoCorrect="off"
        rows={8}
        aria-label="Pytest test code"
      />

      <div className="analyze-row">
        <button
          className="btn btn--run btn--lg"
          onClick={handleRun}
          disabled={loading || !testCode}
          type="button"
          aria-busy={loading}
        >
          {loading ? 'Running…' : 'Run Tests'}
        </button>
        <span className="panel-hint">
          {testCode
            ? 'Execute the test suite against the current source code.'
            : 'Load or paste test code to enable this button.'}
        </span>
      </div>

      {/* Results */}
      {results && (
        <div className="test-results">
          <div className="test-summary-row">
            <span className={`test-status-badge ${results.passed ? 'test-status-badge--pass' : 'test-status-badge--fail'}`}>
              {results.passed ? 'PASS' : 'FAIL'}
            </span>
            {results.timed_out && (
              <span className="badge badge--yellow">Timed out</span>
            )}
            <span className="test-counts">
              {results.tests_total} total &nbsp;·&nbsp;
              <span className="tests-passed">{results.tests_passed} passed</span>
              {results.tests_failed > 0 && (
                <span className="tests-failed"> · {results.tests_failed} failed</span>
              )}
              {results.tests_errors > 0 && (
                <span className="tests-errors"> · {results.tests_errors} errors</span>
              )}
            </span>
            <span className="return-code" title="Process exit code">
              exit {results.returncode}
            </span>
          </div>

          {results.summary && (
            <div className="test-summary-text">
              <pre className="code-block code-block--compact">{results.summary}</pre>
            </div>
          )}

          <button
            className="btn btn--ghost btn--sm"
            onClick={() => setShowOutput((v) => !v)}
            type="button"
            aria-expanded={showOutput}
          >
            {showOutput ? 'Hide output' : 'Show full output'}
          </button>

          {showOutput && (
            <div className="test-output">
              {results.stdout && (
                <>
                  <h4 className="output-label">stdout</h4>
                  <pre className="code-block code-block--compact">{results.stdout}</pre>
                </>
              )}
              {results.stderr && (
                <>
                  <h4 className="output-label">stderr</h4>
                  <pre className="code-block code-block--compact code-block--stderr">{results.stderr}</pre>
                </>
              )}
            </div>
          )}
        </div>
      )}
    </section>
  )
}
