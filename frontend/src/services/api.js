/**
 * api.js
 * ------
 * Centralised API helper for the DebugFlow FastAPI backend.
 *
 * All fetch logic lives here so components stay clean.
 * Base URL is read from the Vite env variable VITE_API_URL,
 * which defaults to http://localhost:8000 for local development.
 */

const BASE_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000'

/**
 * POST /analyze
 *
 * @param {string} code     - Python source code
 * @param {string} error    - Raw traceback / error string
 * @returns {Promise<AnalyzeResponse>}
 */
export async function analyzeCode(code, error) {
  const response = await fetch(`${BASE_URL}/analyze`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ code, error }),
  })
  if (!response.ok) {
    const detail = await _extractErrorDetail(response)
    throw new Error(`Analyze failed (${response.status}): ${detail}`)
  }
  return response.json()
}

/**
 * POST /fix
 *
 * @param {string} code       - Python source code
 * @param {object} analysis   - The root_cause dict from /analyze response
 * @returns {Promise<FixResponse>}
 */
export async function generateFix(code, analysis) {
  const response = await fetch(`${BASE_URL}/fix`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ code, analysis }),
  })
  if (!response.ok) {
    const detail = await _extractErrorDetail(response)
    throw new Error(`Fix generation failed (${response.status}): ${detail}`)
  }
  return response.json()
}

/**
 * POST /run-tests
 *
 * @param {string} testCode   - Pytest-compatible Python test source
 * @param {number} timeout    - Max seconds (default 30)
 * @returns {Promise<RunTestsResponse>}
 */
export async function runTests(testCode, timeout = 30) {
  const response = await fetch(`${BASE_URL}/run-tests`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ test_code: testCode, timeout }),
  })
  if (!response.ok) {
    const detail = await _extractErrorDetail(response)
    throw new Error(`Run tests failed (${response.status}): ${detail}`)
  }
  return response.json()
}

/**
 * GET /health
 * Quick liveness check — used on load to warn if backend is down.
 */
export async function checkHealth() {
  const response = await fetch(`${BASE_URL}/health`)
  if (!response.ok) throw new Error('Backend health check failed')
  return response.json()
}

// ── Internal helpers ──────────────────────────────────────────────────────────

async function _extractErrorDetail(response) {
  try {
    const body = await response.json()
    return body.detail || JSON.stringify(body)
  } catch {
    return response.statusText
  }
}
