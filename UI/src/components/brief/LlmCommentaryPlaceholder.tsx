export function LlmCommentaryPlaceholder() {
  return (
    <div className="flex flex-col items-center justify-center rounded-lg border border-dashed border-zinc-700 bg-zinc-900/20 px-6 py-12 text-center">
      <span className="text-2xl text-zinc-600" aria-hidden>
        ◈
      </span>
      <p className="mt-3 text-sm font-medium text-zinc-400">LLM commentary — coming soon</p>
      <p className="mt-1 max-w-sm text-xs text-zinc-600">
        Narrative interpretation of current regime + key risks
      </p>
    </div>
  )
}
