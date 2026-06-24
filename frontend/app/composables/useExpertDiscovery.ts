import { api } from "~/utils/api"

export interface EvidenceDoc {
  title: string
  patent_id: string
  role: string
}

export interface ExpertOutput {
  rank: number
  name: string
  score: number
  expertise: string[]
  reasoning: string
  evidence: EvidenceDoc[]
  contact: {
    organization: string | null
  } | null
}

export interface DiscoverExpertsResponse {
  query: string
  xsearch_id: string | null
  total_documents_found: number
  raw_documents: any[]
  experts: ExpertOutput[]
}

export function useExpertDiscovery() {
  async function discoverExperts(
    query: string,
    topK: number = 5
  ): Promise<DiscoverExpertsResponse> {
    const res = await api.post("/discover-experts", {
      query,
      top_k: topK,
    })
    return res.data as DiscoverExpertsResponse
  }

  return { discoverExperts }
}
