interface StepData {
  label: string
  number: number
  state: 'done' | 'active' | 'pending'
}

interface StepperProps {
  steps: StepData[]
}

export default function Stepper({ steps }: StepperProps) {
  return (
    <div className="stepper">
      {steps.map((step, i) => (
        <div key={i}>
          <div className={`step ${step.state}`}>
            <div className="step-dot">{step.state === 'done' ? '✓' : step.number}</div>
            <div className="step-text">{step.label}</div>
          </div>
          {i < steps.length - 1 && <div className={`step-line ${step.state === 'done' ? 'done' : ''}`} />}
        </div>
      ))}
    </div>
  )
}