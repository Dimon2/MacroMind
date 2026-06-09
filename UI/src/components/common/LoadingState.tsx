export function LoadingState({ message = 'Loading…' }: { message?: string }) {
  return (
    <div className="flex items-center justify-center py-16 text-zinc-500">
      <span className="animate-pulse">{message}</span>
    </div>
  )
}
