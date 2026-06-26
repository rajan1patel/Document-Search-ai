import { api } from "~/utils/api"

export interface ResearchExpertOutput {
  author_id: string
  author: string
  score: number
  metrics: {
    works_count: number
    citations: number
    h_index: number
  }
  matched_topic: {
    topic_name: string
    topic_count: number
  } | null
  all_topics: {
    topic_name: string
    count: number
    subfield: string
  }[]
  why: string[]
  institution: string
  first_year: number
  last_year: number
  openalex_url: string
}

export interface ResearchExpertResponse {
  query: string
  total_works_found: number
  total_authors_extracted: number
  experts: ResearchExpertOutput[]
}

export function useResearchExpert() {
  async function searchExperts(
    query: string,
    topK: number = 20
  ): Promise<ResearchExpertResponse> {
    const res = await api.post("/experts/search", {
      query,
      top_k: topK,
    })
    return res.data as ResearchExpertResponse
  }

  return { searchExperts }
}
