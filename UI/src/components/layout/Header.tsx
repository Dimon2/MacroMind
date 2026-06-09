export function Header() {
  return (
    <header className="border-b border-zinc-800 bg-zinc-950/80 backdrop-blur-sm">
      <div className="mx-auto flex max-w-6xl items-center justify-between px-4 py-4">
        <div>
          <h1 className="text-lg font-semibold tracking-tight text-zinc-100">
            MacroMind
          </h1>
          <p className="text-xs text-zinc-500">Personal macro & risk desk</p>
        </div>
      </div>
    </header>
  )
}
