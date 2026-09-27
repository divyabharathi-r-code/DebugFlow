/**
 * WorkflowStatus.jsx
 * ------------------
 * Displays a linear progress indicator for the 6-stage debug workflow.
 */

const STAGES = [
  { id: 'idle',       label: 'Input' },
  { id: 'analyzing', label: 'Analyze' },
  { id: 'analyzed',  label: 'Root Cause' },
  { id: 'fixing',    label: 'Fix' },
  { id: 'testing',   label: 'Test' },
  { id: 'verified',  label: 'Verified' },
]

// Map app stage names to a numeric index for comparison
const STAGE_INDEX = {
  idle:       0,
  analyzing:  1,
  analyzed:   2,
  fixing:     3,
  fixed:      3,
  testing:    4,
  verified:   5,
}

// Dynamic label overrides per app stage
const STAGE_LABEL_OVERRIDE = {
  analyzing: 'Analyzing…',
  fixing:    'Generating…',
  testing:   'Running…',
}

export default function WorkflowStatus({ stage }) {
  const currentIndex = STAGE_INDEX[stage] ?? 0

  return (
    <nav className="workflow-status" aria-label="Debug pipeline progress">
      <span className="workflow-status-label" aria-hidden="true">Pipeline</span>
      {STAGES.map((s, idx) => {
        let state = 'pending'
        if (idx < currentIndex) state = 'done'
        else if (idx === currentIndex) state = 'active'

        const label =
          state === 'active' && STAGE_LABEL_OVERRIDE[stage]
            ? STAGE_LABEL_OVERRIDE[stage]
            : s.label

        return (
          <div key={s.id} className={`workflow-step workflow-step--${state}`}>
            <div className="workflow-node" aria-hidden="true">
              {state === 'done' ? '✓' : idx + 1}
            </div>
            <span className="workflow-label">{label}</span>
            {idx < STAGES.length - 1 && (
              <div
                className={`workflow-connector workflow-connector--${state === 'done' ? 'done' : 'pending'}`}
                aria-hidden="true"
              />
            )}
          </div>
        )
      })}
    </nav>
  )
}
