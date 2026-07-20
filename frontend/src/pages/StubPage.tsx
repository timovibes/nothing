export function StubPage({ title }: { title: string }) {
  return (
    <div>
      <p className="text-xs uppercase tracking-wide text-secondary mb-2">{title}</p>
      <p className="text-secondary text-sm">This page hasn't been built yet.</p>
    </div>
  );
}