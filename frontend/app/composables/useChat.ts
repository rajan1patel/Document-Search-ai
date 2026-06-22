import { api } from "~/utils/api"

export interface Source {
  filename: string | null
  page: number | null
  chunk: string
  score: number
}

export interface Message {
  role: "user" | "assistant"
  content: string
  sources?: Source[]
}

export function useChat() {
  async function sendMessage(
    query: string,
    history: Message[],
    limit: number = 5
  ): Promise<{ answer: string; sources: Source[] }> {
    const historyPayload = history.map((m) => ({
      role: m.role,
      content: m.content,
    }))

    const res = await api.post("/chat", {
      query,
      limit,
      history: historyPayload,
    })

    return {
      answer: res.data.answer,
      sources: res.data.sources,
    }
  }

  return { sendMessage }
}
