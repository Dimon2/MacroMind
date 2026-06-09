import { Outlet } from 'react-router-dom'
import { Header } from './Header'
import { Nav } from './Nav'

export function AppShell() {
  return (
    <div className="flex min-h-svh flex-col">
      <Header />
      <div className="border-b border-zinc-800">
        <div className="mx-auto flex max-w-6xl px-4 py-2">
          <Nav />
        </div>
      </div>
      <main className="mx-auto w-full max-w-6xl flex-1 px-4 py-6">
        <Outlet />
      </main>
    </div>
  )
}
