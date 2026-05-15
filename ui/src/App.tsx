import { BrowserRouter, Routes, Route } from 'react-router-dom'
import { Shell } from './components/layout'
import {
  Marketplace,
  VaultDetail,
  PortfolioDashboard,
  StrategyExplorer,
  Swap,
  VaultCreator,
  Onboarding,
  ReasoningTrace,
} from './pages'
import './styles/globals.css'

export default function App() {
  return (
    <BrowserRouter>
      <Routes>
        <Route path="/" element={<Onboarding />} />
        <Route element={<Shell />}>
          <Route path="/explore" element={<Marketplace />} />
          <Route path="/vault/:id" element={<VaultDetail />} />
          <Route path="/dashboard" element={<PortfolioDashboard />} />
          <Route path="/strategies" element={<StrategyExplorer />} />
          <Route path="/trade" element={<Swap />} />
          <Route path="/create-vault" element={<VaultCreator />} />
          <Route path="/reasoning" element={<ReasoningTrace />} />
          <Route path="/reasoning/:id" element={<ReasoningTrace />} />
        </Route>
      </Routes>
    </BrowserRouter>
  )
}