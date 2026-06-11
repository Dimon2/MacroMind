type DataNotesProps = {
  notes: string[]
}

function noteClassName(note: string): string {
  if (note.includes('skipped')) {
    return 'text-amber-400/90'
  }
  return 'text-zinc-500'
}

export function DataNotes({ notes }: DataNotesProps) {
  if (notes.length === 0) return null

  return (
    <details className="rounded-lg border border-zinc-800 bg-zinc-900/40 px-4 py-3">
      <summary className="cursor-pointer text-sm font-medium text-zinc-400">
        Data notes ({notes.length})
      </summary>
      <ul className="mt-3 space-y-2 text-xs">
        {notes.map((note) => (
          <li key={note} className={noteClassName(note)}>
            {note}
          </li>
        ))}
      </ul>
    </details>
  )
}
