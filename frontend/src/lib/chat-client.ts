import type {
  ChatRequest,
  ChatResponse,
  NormalizedChatResponse,
  StructuredUiBlock
} from "@/lib/chat-types";

const DEFAULT_CHAT_ENDPOINT = "/api/chat";

function normalizeBlocks(payload: ChatResponse): StructuredUiBlock[] {
  const structuredBlocks = payload.structuredUi ?? payload.uiComponents ?? payload.ui_components ?? [];

  if (!payload.clarifying_question) {
    return structuredBlocks;
  }

  return [
    {
      type: "clarifying_question",
      question: payload.clarifying_question,
      options: payload.next_actions
    },
    ...structuredBlocks
  ];
}

export async function sendChatMessage(
  request: ChatRequest,
  endpoint = process.env.NEXT_PUBLIC_CHAT_ENDPOINT ?? DEFAULT_CHAT_ENDPOINT
): Promise<NormalizedChatResponse> {
  const response = await fetch(endpoint, {
    method: "POST",
    headers: {
      "Content-Type": "application/json"
    },
    body: JSON.stringify(request)
  });

  if (!response.ok) {
    const errorText = await response.text();
    throw new Error(errorText || `Chat request failed with status ${response.status}`);
  }

  const data = (await response.json()) as ChatResponse;

  return {
    sessionId: data.sessionId ?? request.sessionId,
    assistantMessage: data.assistantMessage ?? data.message ?? data.summary ?? "",
    structuredBlocks: normalizeBlocks(data)
  };
}

