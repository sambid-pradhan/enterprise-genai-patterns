"use client";

import type { StructuredUiBlock } from "@/lib/chat-types";

type StructuredRendererProps = {
  blocks?: StructuredUiBlock[];
  onAction?: (value: string) => void;
};

function isRenderableItem(item: string | { label: string; description?: string }) {
  return typeof item === "string" ? { label: item } : item;
}

export function StructuredRenderer({ blocks, onAction }: StructuredRendererProps) {
  if (!blocks?.length) {
    return null;
  }

  return (
    <div className="structured-stack">
      {blocks.map((block, index) => {
        if (block.type === "recipe_card") {
          return (
            <article className="structured-card" key={`${block.type}-${block.title}-${index}`}>
              <div className="structured-card__header">
                <div>
                  <p className="structured-kicker">Recipe card</p>
                  <h3 className="structured-card__title">{block.title}</h3>
                </div>
                <div className="structured-card__meta">
                  {block.prepTimeMinutes ? <span>{block.prepTimeMinutes} min prep</span> : null}
                  {block.cookTimeMinutes ? <span>{block.cookTimeMinutes} min cook</span> : null}
                  {block.servings ? <span>{block.servings}</span> : null}
                </div>
              </div>

              {block.summary ? <p className="structured-card__summary">{block.summary}</p> : null}

              {block.tags?.length ? (
                <div className="pill-row" aria-label="Recipe tags">
                  {block.tags.map((tag) => (
                    <span className="pill" key={tag}>
                      {tag}
                    </span>
                  ))}
                </div>
              ) : null}

              {block.ingredients?.length ? (
                <section className="structured-section">
                  <h4>Ingredients</h4>
                  <ul className="structured-list">
                    {block.ingredients.map((ingredient) => (
                      <li key={ingredient}>{ingredient}</li>
                    ))}
                  </ul>
                </section>
              ) : null}

              {block.steps?.length ? (
                <section className="structured-section">
                  <h4>Steps</h4>
                  <ol className="structured-list structured-list--ordered">
                    {block.steps.map((step) => (
                      <li key={step}>{step}</li>
                    ))}
                  </ol>
                </section>
              ) : null}
            </article>
          );
        }

        if (block.type === "clarifying_question") {
          return (
            <section className="clarifying-card" key={`${block.type}-${index}`}>
              <p className="structured-kicker">Clarifying question</p>
              <h3 className="clarifying-card__question">{block.question}</h3>
              {block.options?.length ? (
                <div className="clarifying-actions" role="group" aria-label="Suggested replies">
                  {block.options.map((option) => (
                    <button
                      className="clarifying-actions__button"
                      key={option}
                      type="button"
                      onClick={() => onAction?.(option)}
                    >
                      {option}
                    </button>
                  ))}
                </div>
              ) : null}
            </section>
          );
        }

        return (
          <section className="structured-card" key={`${block.type}-${block.title ?? "list"}-${index}`}>
            {block.title ? <h3 className="structured-card__title">{block.title}</h3> : null}
            <div className="structured-list-block">
              {block.ordered ? (
                <ol className="structured-list structured-list--ordered">
                  {block.items.map((item) => {
                    const entry = isRenderableItem(item);
                    return (
                      <li key={entry.label}>
                        <span className="structured-list__label">{entry.label}</span>
                        {entry.description ? (
                          <span className="structured-list__description">{entry.description}</span>
                        ) : null}
                      </li>
                    );
                  })}
                </ol>
              ) : (
                <ul className="structured-list">
                  {block.items.map((item) => {
                    const entry = isRenderableItem(item);
                    return (
                      <li key={entry.label}>
                        <span className="structured-list__label">{entry.label}</span>
                        {entry.description ? (
                          <span className="structured-list__description">{entry.description}</span>
                        ) : null}
                      </li>
                    );
                  })}
                </ul>
              )}
            </div>
          </section>
        );
      })}
    </div>
  );
}

