export default function Logo() {
  return (
    <div className="sidebar-brand">
      <div className="logo">
        <div className="logo-mark">
          <svg viewBox="0 0 16 16" fill="none">
            <path d="M8 1L14 5v6l-6 4-6-4V5l6-4z" stroke="#09090B" strokeWidth="1.5"/>
            <circle cx="8" cy="8" r="2.5" stroke="#09090B" strokeWidth="1.5"/>
          </svg>
        </div>
        <div>
          <div className="logo-text">Archimedes</div>
          <div className="logo-sub">Portfolio Intelligence</div>
        </div>
      </div>
    </div>
  )
}