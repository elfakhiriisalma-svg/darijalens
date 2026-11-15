export type View = "analysis" | "dashboard";

export function Brand() {
  return (
    <div className="brand-lockup">
      <span className="brand-mark" aria-hidden="true">
        د
      </span>
      <span className="brand-name">DarijaLens</span>
    </div>
  );
}

interface NavProps {
  view: View;
  onChange: (view: View) => void;
}

export function Nav({ view, onChange }: NavProps) {
  const items: { id: View; label: string }[] = [
    { id: "analysis", label: "Analyse" },
    { id: "dashboard", label: "Tableau de bord" },
  ];
  return (
    <nav className="nav" aria-label="Sections">
      {items.map((item) => (
        <button
          key={item.id}
          type="button"
          aria-current={view === item.id ? "page" : undefined}
          onClick={() => onChange(item.id)}
        >
          {item.label}
        </button>
      ))}
    </nav>
  );
}
