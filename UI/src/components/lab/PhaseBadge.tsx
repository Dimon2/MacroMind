import type { StressPhase } from '../../types/regimeLab'

const PHASE_STYLES: Record<StressPhase, string> = {
  detection: 'border-amber-800/60 bg-amber-900/30 text-amber-300',
  recovery: 'border-emerald-800/60 bg-emerald-900/30 text-emerald-300',
  stress: 'border-orange-800/60 bg-orange-900/30 text-orange-300',
  mini_crisis: 'border-rose-800/60 bg-rose-900/30 text-rose-300',
  false_alarm: 'border-sky-800/60 bg-sky-900/30 text-sky-300',
}

type PhaseBadgeProps = {
  phase: StressPhase
}

export function PhaseBadge({ phase }: PhaseBadgeProps) {
  return (
    <span
      className={`inline-flex rounded border px-1.5 py-0.5 text-[10px] font-medium uppercase tracking-wide ${PHASE_STYLES[phase]}`}
    >
      {phase.replace('_', ' ')}
    </span>
  )
}
