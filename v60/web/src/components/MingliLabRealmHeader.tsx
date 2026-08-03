export function MingliLabRealmHeader({
  backLabel,
  eyebrow,
  onBack,
  status,
  title,
}: {
  backLabel: string;
  eyebrow: string;
  onBack: () => void;
  status?: string;
  title: string;
}) {
  return (
    <header className="mingli-lab-realm-header">
      <button onClick={onBack} type="button">
        <span aria-hidden="true">←</span>
        {backLabel}
      </button>
      <div>
        <small>{eyebrow}</small>
        <strong>{title}</strong>
      </div>
      <span>{status ?? "研究方法 · 真实目录"}</span>
    </header>
  );
}
