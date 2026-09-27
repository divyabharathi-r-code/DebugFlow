/**
 * App.jsx
 * -------
 * Root application component.
 * Manages all state and orchestrates API calls.
 *
 * Workflow stages:
 *   idle → analyzing → analyzed → fixing → fixed → testing → verified
 */

import { useState, useEffect } from 'react'
import Header from './components/Header.jsx'
import WorkflowStatus from './components/WorkflowStatus.jsx'
import CodeInput from './components/CodeInput.jsx'
import ErrorInput from './components/ErrorInput.jsx'
import AnalysisPanel from './components/AnalysisPanel.jsx'
import FixPanel from './components/FixPanel.jsx'
import TestResults from './components/TestResults.jsx'
import { analyzeCode, generateFix, runTests, checkHealth } from './services/api.js'

export default function App() {
  // ── Inputs ──────────────────────────────────────────────────────────────────
  const [code, setCode] = useState('')
  const [error, setError] = useState('')

  // ── Workflow ─────────────────────────────────────────────────────────────────
  const [stage, setStage] = useState('idle')
  const [backendStatus, setBackendStatus] = useState('checking')

  // ── Results ──────────────────────────────────────────────────────────────────
  const [analysisResult, setAnalysisResult] = useState(null)
  const [fixResult, setFixResult] = useState(null)
  const [testResult, setTestResult] = useState(null)

  // ── Loading flags ────────────────────────────────────────────────────────────
  const [analyzeLoading, setAnalyzeLoading] = useState(false)
  const [fixLoading, setFixLoading] = useState(false)
  const [testLoading, setTestLoading] = useState(false)

  // ── Global error banner ───────────────────────────────────────────────────────
  const [appError, setAppError] = useState(null)

  // ── Health check on mount ─────────────────────────────────────────────────────
  useEffect(() => {
    checkHealth()
      .then(() => setBackendStatus('online'))
      .catch(() => setBackendStatus('offline'))
  }, [])

  // ── Workflow reset helper ─────────────────────────────────────────────────────
  /** Clear all results and return to idle — called when demo inputs change. */
  function resetWorkflow() {
    setAnalysisResult(null)
    setFixResult(null)
    setTestResult(null)
    setStage('idle')
    setAppError(null)
  }

  /** Wrap setCode so loading new demo code also resets downstream results. */
  function handleSetCode(newCode) {
    setCode(newCode)
    resetWorkflow()
  }

  /** Wrap setError so loading a new demo error also resets downstream results. */
  function handleSetError(newError) {
    setError(newError)
    resetWorkflow()
  }

  // ── Handlers ─────────────────────────────────────────────────────────────────

  async function handleAnalyze() {
    setAppError(null)

    if (!code.trim()) {
      setAppError('Please enter some Python source code before analyzing.')
      return
    }
    if (!error.trim()) {
      setAppError('Please enter a traceback or error message before analyzing.')
      return
    }
    if (backendStatus === 'offline') {
      setAppError('The DebugFlow backend is not reachable. Make sure it is running on port 8000.')
      return
    }

    setAnalyzeLoading(true)
    setStage('analyzing')
    setAnalysisResult(null)
    setFixResult(null)
    setTestResult(null)

    try {
      const data = await analyzeCode(code, error)
      setAnalysisResult(data.root_cause)
      setStage('analyzed')
    } catch (err) {
      setAppError(friendlyError('Analysis', err))
      setStage('idle')
    } finally {
      setAnalyzeLoading(false)
    }
  }

  async function handleGenerateFix() {
    if (!analysisResult) return
    setAppError(null)
    setFixLoading(true)
    setStage('fixing')
    setFixResult(null)

    try {
      const data = await generateFix(code, analysisResult)
      setFixResult(data)
      setStage('fixed')
    } catch (err) {
      setAppError(friendlyError('Fix generation', err))
      setStage('analyzed')
    } finally {
      setFixLoading(false)
    }
  }

  async function handleRunTests(testCode) {
    setAppError(null)
    setTestLoading(true)
    setStage('testing')
    setTestResult(null)

    try {
      const data = await runTests(testCode)
      setTestResult(data)
      setStage(data.passed ? 'verified' : 'fixed')
    } catch (err) {
      setAppError(friendlyError('Test run', err))
      setStage('fixed')
    } finally {
      setTestLoading(false)
    }
  }

  /** When user clicks "Apply Fix", copy the fixed code back to the editor */
  function handleApplyFix(fixedCode) {
    setCode(fixedCode)
    // Reset downstream results so user knows to re-analyze
    setAnalysisResult(null)
    setFixResult(null)
    setTestResult(null)
    setStage('idle')
    setAppError(null)
  }

  // ── Render ───────────────────────────────────────────────────────────────────
  return (
    <div className="app">
      <Header backendStatus={backendStatus} />

      <main className="app-main">
        {/* Global error banner */}
        {appError && (
          <div className="error-banner" role="alert">
            <strong>Error: </strong>{appError}
            <button
              className="error-banner-close"
              onClick={() => setAppError(null)}
              type="button"
              aria-label="Dismiss error"
            >
              ✕
            </button>
          </div>
        )}

        {/* Offline warning */}
        {backendStatus === 'offline' && (
          <div className="warn-banner" role="alert">
            Cannot reach the backend at <code>localhost:8000</code>.
            Start it with: <code>uvicorn main:app --reload</code> inside the <code>backend/</code> folder.
          </div>
        )}

        {/* Workflow progress bar */}
        <WorkflowStatus stage={stage} />

        {/* Two-column input row */}
        <div className="input-row">
          <CodeInput code={code} onChange={handleSetCode} />
          <ErrorInput
            error={error}
            onChange={handleSetError}
            onAnalyze={handleAnalyze}
            loading={analyzeLoading}
          />
        </div>

        {/* Analysis result */}
        {analysisResult && (
          <AnalysisPanel
            analysis={analysisResult}
            onRequestFix={handleGenerateFix}
            fixLoading={fixLoading}
          />
        )}

        {/* Fix result */}
        {fixResult && (
          <FixPanel fix={fixResult} onApplyFix={handleApplyFix} />
        )}

        {/* Test runner — always shown */}
        <TestResults
          results={testResult}
          onRunTests={handleRunTests}
          loading={testLoading}
        />
      </main>

      <footer className="app-footer">
        <span>DebugFlow · Hackathon MVP · Powered by FastAPI + React</span>
      </footer>
    </div>
  )
}

// ── Helpers ───────────────────────────────────────────────────────────────────

function friendlyError(context, err) {
  const msg = err?.message || String(err)
  if (msg.includes('Failed to fetch') || msg.includes('NetworkError') || msg.includes('fetch')) {
    return `${context} failed: Cannot reach the backend. Is it running on port 8000?`
  }
  return `${context} failed: ${msg}`
}
