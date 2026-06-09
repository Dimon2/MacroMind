export function ErrorState({ message }: { message: string }) {
  return (
    <div className="rounded-lg border border-red-900/50 bg-red-950/30 px-4 py-6 text-red-300">
      {message}
    </div>
  )
}
