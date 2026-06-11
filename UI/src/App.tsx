import { Navigate, Route, Routes } from 'react-router-dom'
import { AppShell } from './components/layout/AppShell'
import { BriefPage } from './pages/BriefPage'
import { DeskPage } from './pages/DeskPage'
import { MacroPage } from './pages/MacroPage'
import { NotFoundPage } from './pages/NotFoundPage'
import { RegimeLabPage } from './pages/RegimeLabPage'

export default function App() {
  return (
    <Routes>
      <Route element={<AppShell />}>
        <Route index element={<BriefPage />} />
        <Route path="desk" element={<DeskPage />} />
        <Route path="lab/regimes" element={<RegimeLabPage />} />
        <Route path="macro/:seriesId" element={<MacroPage />} />
        <Route path="404" element={<NotFoundPage />} />
        <Route path="*" element={<Navigate to="/404" replace />} />
      </Route>
    </Routes>
  )
}
