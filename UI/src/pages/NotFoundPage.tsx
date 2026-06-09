import { Link } from 'react-router-dom'

export function NotFoundPage() {
  return (
    <div className="py-16 text-center">
      <p className="text-4xl font-semibold text-zinc-600">404</p>
      <p className="mt-2 text-zinc-400">Page not found</p>
      <Link
        to="/"
        className="mt-6 inline-block rounded-md bg-zinc-800 px-4 py-2 text-sm text-zinc-200 hover:bg-zinc-700"
      >
        Back to desk
      </Link>
    </div>
  )
}
