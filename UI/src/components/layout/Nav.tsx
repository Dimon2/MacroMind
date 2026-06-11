import { NavLink } from 'react-router-dom'

const linkClass = ({ isActive }: { isActive: boolean }) =>
  [
    'rounded-md px-3 py-1.5 text-sm font-medium transition-colors',
    isActive
      ? 'bg-zinc-800 text-zinc-100'
      : 'text-zinc-400 hover:bg-zinc-900 hover:text-zinc-200',
  ].join(' ')

export function Nav() {
  return (
    <nav className="flex gap-1">
      <NavLink to="/" end className={linkClass}>
        Brief
      </NavLink>
      <NavLink to="/desk" className={linkClass}>
        Desk
      </NavLink>
      <NavLink to="/lab/regimes" className={linkClass}>
        Lab
      </NavLink>
    </nav>
  )
}
