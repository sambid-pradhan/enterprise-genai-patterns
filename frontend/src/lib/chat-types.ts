export type ChatRole = "user" | "assistant";

export type RecipeCardBlock = {
  type: "recipe_card";
  title: string;
  summary?: string;
  prepTimeMinutes?: number;
  cookTimeMinutes?: number;
  servings?: string;
  ingredients?: string[];
  steps?: string[];
  tags?: string[];
};

export type ClarifyingQuestionBlock = {
  type: "clarifying_question";
  question: string;
  options?: string[];
};

export type ListBlock = {
  type: "list";
  title?: string;
  ordered?: boolean;
  items: Array<string | { label: string; description?: string }>;
};

export type StructuredUiBlock = RecipeCardBlock | ClarifyingQuestionBlock | ListBlock;

export type ChatMessage = {
  id: string;
  role: ChatRole;
  content: string;
  structuredBlocks?: StructuredUiBlock[];
  isPending?: boolean;
  isError?: boolean;
};

export type ChatTurn = {
  role: ChatRole;
  content: string;
};

export type ChatRequest = {
  sessionId: string;
  message: string;
  history?: ChatTurn[];
};

export type ChatResponse = {
  sessionId?: string;
  assistantMessage?: string;
  message?: string;
  summary?: string;
  structuredUi?: StructuredUiBlock[];
  uiComponents?: StructuredUiBlock[];
  ui_components?: StructuredUiBlock[];
  clarifying_question?: string;
  next_actions?: string[];
};

export type NormalizedChatResponse = {
  sessionId: string;
  assistantMessage: string;
  structuredBlocks: StructuredUiBlock[];
};

