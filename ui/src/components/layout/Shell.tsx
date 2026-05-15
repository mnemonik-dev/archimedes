import { Outlet } from 'react-router-dom'
import Sidebar from './Sidebar'

export default function Shell() {
  return (
    <div className="shell">
      <Sidebar />
      <div className="main">
        <Outlet />
      </div>
    </div>
  )
}