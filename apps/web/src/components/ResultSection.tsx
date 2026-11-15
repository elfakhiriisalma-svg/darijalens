import type { ReactNode } from "react";
import type { Verdict } from "../lib/format";
import type { Outcome } from "../types";

interface ResultSectionProps<T> {
  title: string;
  question: string;
  outcome: Outcome<T>;
  verdict: (data: T) => Verdict;
  children: (data: T) => ReactNode;
}

/** Un bloc de résultat : titre, verdict en grand, détail, puis le contenu (échelle, etc.). */
export function ResultSection<T>({ title, question, outcome, verdict, children }: ResultSectionProps<T>) {
  return (
    <section className="result" aria-label={title}>
      <h2>{title}</h2>
      <p className="question">{question}</p>
      {outcome.ok ? (
        <>
          <p className={`verdict tone-${verdict(outcome.data).tone}`}>{verdict(outcome.data).title}</p>
          <p className="detail">{verdict(outcome.data).detail}</p>
          {children(outcome.data)}
        </>
      ) : (
        <p className="problem" role="alert">
          {outcome.message}
        </p>
      )}
    </section>
  );
}
