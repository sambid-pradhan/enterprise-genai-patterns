import { render, screen } from "@testing-library/react";
import { StructuredRenderer } from "@/components/structured-renderer";
import type { StructuredUiBlock } from "@/lib/chat-types";

describe("StructuredRenderer", () => {
  it("renders recipe cards with ingredients and steps", () => {
    const blocks: StructuredUiBlock[] = [
      {
        type: "recipe_card",
        title: "Weeknight Chili",
        summary: "A fast, hearty bowl with pantry ingredients.",
        prepTimeMinutes: 10,
        cookTimeMinutes: 25,
        servings: "Serves 4",
        tags: ["high protein", "budget"],
        ingredients: ["1 lb ground turkey", "1 can beans"],
        steps: ["Brown the turkey.", "Simmer with beans and spices."]
      }
    ];

    render(<StructuredRenderer blocks={blocks} />);

    expect(screen.getByRole("heading", { name: "Weeknight Chili" })).toBeInTheDocument();
    expect(screen.getByText("A fast, hearty bowl with pantry ingredients.")).toBeInTheDocument();
    expect(screen.getByText("Ingredients")).toBeInTheDocument();
    expect(screen.getByText("Steps")).toBeInTheDocument();
    expect(screen.getByText("high protein")).toBeInTheDocument();
  });

  it("renders clarifying questions as actionable prompts", () => {
    const onAction = vi.fn();
    const blocks: StructuredUiBlock[] = [
      {
        type: "clarifying_question",
        question: "What spice level do you want?",
        options: ["Mild", "Medium", "Hot"]
      }
    ];

    render(<StructuredRenderer blocks={blocks} onAction={onAction} />);

    expect(screen.getByRole("heading", { name: "What spice level do you want?" })).toBeInTheDocument();
    expect(screen.getByRole("button", { name: "Mild" })).toBeInTheDocument();
    screen.getByRole("button", { name: "Hot" }).click();
    expect(onAction).toHaveBeenCalledWith("Hot");
  });

  it("renders list blocks in the expected order", () => {
    const blocks: StructuredUiBlock[] = [
      {
        type: "list",
        title: "Next steps",
        ordered: true,
        items: [
          { label: "Check pantry", description: "Confirm ingredients on hand." },
          "Send the refined request"
        ]
      }
    ];

    render(<StructuredRenderer blocks={blocks} />);

    expect(screen.getByRole("heading", { name: "Next steps" })).toBeInTheDocument();
    expect(screen.getByText("Check pantry")).toBeInTheDocument();
    expect(screen.getByText("Send the refined request")).toBeInTheDocument();
  });
});

