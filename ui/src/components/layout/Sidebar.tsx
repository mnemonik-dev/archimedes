import { NavLink } from 'react-router-dom'
import Logo from './Logo'

const NAV_GROUPS = [
  {
    group: 'Markets',
    items: [
      { to: '/explore', label: 'Explore' },
      { to: '/strategies', label: 'Strategies' },
      { to: '/trade', label: 'Trade' },
    ],
  },
  {
    group: 'Portfolio',
    items: [
      { to: '/dashboard', label: 'Dashboard' },
      { to: '/create-vault', label: 'Create Vault' },
    ],
  },
  {
    group: 'Intelligence',
    items: [
      { to: '/reasoning', label: 'Reasoning' },
    ],
  },
]

export default function Sidebar() {
  return (
    <aside className="sidebar">
      <Logo />
      <nav>
        {NAV_GROUPS.map(({ group, items }) => (
          <div key={group} className="nav-group">
            <div className="nav-group-label">{group}</div>
            {items.map(({ to, label }) => (
              <NavLink key={to} to={to} className={({ isActive }) => `nav-link${isActive ? ' active' : ''}`}>
                {label}
              </NavLink>
            ))}
          </div>
        ))}
      </nav>
      <div className="sidebar-footer">
        <div className="caption" style={{ display: 'flex', alignItems: 'center', gap: 6 }}>
          <span style={{ width: 6, height: 6, borderRadius: '50%', background: 'var(--positive)' }} />
          Arc · Block 1,247,892
        </div>
      </div>
    </aside>
  )
}