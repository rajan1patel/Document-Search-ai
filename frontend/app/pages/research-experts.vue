<script setup lang="ts">
definePageMeta({
  middleware: "auth",
})

import { ref, computed, onMounted } from "vue"
import { useResearchExpert, type ResearchExpertOutput, type ResearchExpertResponse } from "~/composables/useResearchExpert"

const { searchExperts } = useResearchExpert()

const query = ref("quantum error correction")
const loading = ref(false)
const error = ref<string | null>(null)
const result = ref<ResearchExpertResponse | null>(null)
const selectedIndex = ref<number | null>(null)

onMounted(() => {
  const mock = JSON.parse(JSON.stringify(MOCK_RESULT))
  result.value = mock
  // Don't auto-select — right panel stays hidden until user clicks
  selectedIndex.value = null
})
const selectedExpert = computed<ResearchExpertOutput | null>(() => {
  if (selectedIndex.value === null || !result.value) return null
  const expert = result.value.experts[selectedIndex.value]
  return expert ?? null
})

const exampleQueries = [
  "quantum error correction",
  "lithium battery thermal management",
  "carbon nanotube interconnects",
  "deep learning for medical imaging",
]

// ── Mock data ──────────────────────────────────────────────
const MOCK_RESULT: ResearchExpertResponse = {
  query: "quantum error correction",
  total_works_found: 1847,
  total_authors_extracted: 312,
  experts: [
    {
      author_id: "A0001",
      author: "Dr. Sarah Chen",
      score: 94.2,
      metrics: { works_count: 187, citations: 15230, h_index: 62 },
      matched_topic: { topic_name: "Quantum Error Correction", topic_count: 34 },
      all_topics: [
        { topic_name: "Quantum Error Correction", count: 34, subfield: "Quantum Computing" },
        { topic_name: "Topological Quantum Codes", count: 28, subfield: "Quantum Information" },
        { topic_name: "Surface Codes", count: 22, subfield: "Quantum Computing" },
        { topic_name: "Fault-tolerant Quantum Computation", count: 18, subfield: "Quantum Computing" },
        { topic_name: "Quantum LDPC Codes", count: 15, subfield: "Information Theory" },
        { topic_name: "Stabilizer Formalism", count: 12, subfield: "Quantum Information" },
      ],
      why: [
        "34 publications match this research problem",
        "High topic concentration in quantum error correction",
        "Active researcher — published consistently in last 5 years",
        "Leading authority on surface code implementations",
        "Highly cited with h-index of 62",
      ],
      institution: "MIT",
      first_year: 2008,
      last_year: 2025,
      openalex_url: "https://openalex.org/A0001",
      orcid: "0000-0001-2345-6789",
      contacts: [
        { type: "email", value: "schen@mit.edu", label: "Email", source: "ORCID" },
        { type: "url", value: "https://sarahchen-lab.mit.edu", label: "Lab Website", source: "ORCID" },
        { type: "url", value: "https://linkedin.com/in/sarahchen", label: "LinkedIn", source: "ORCID" },
      ],
    },
    {
      author_id: "A0002",
      author: "Prof. Michael Torres",
      score: 88.7,
      metrics: { works_count: 142, citations: 9870, h_index: 48 },
      matched_topic: { topic_name: "Quantum Error Correction", topic_count: 27 },
      all_topics: [
        { topic_name: "Quantum Error Correction", count: 27, subfield: "Quantum Computing" },
        { topic_name: "Bosonic Codes", count: 21, subfield: "Quantum Information" },
        { topic_name: "Cat Qubits", count: 17, subfield: "Quantum Computing" },
        { topic_name: "Continuous-variable Quantum Information", count: 14, subfield: "Quantum Optics" },
      ],
      why: [
        "27 publications match this research problem",
        "Pioneer in bosonic error correction codes",
        "Strong citation impact in the field",
        "Active collaborator with top quantum labs",
      ],
      institution: "Caltech",
      first_year: 2010,
      last_year: 2025,
      openalex_url: "https://openalex.org/A0002",
      orcid: "0000-0002-3456-7890",
      contacts: [
        { type: "email", value: "mtorres@caltech.edu", label: "Email", source: "ORCID" },
        { type: "url", value: "https://linkedin.com/in/michaeltorres", label: "LinkedIn", source: "ORCID" },
      ],
    },
    {
      author_id: "A0003",
      author: "Dr. Emily Nakamura",
      score: 82.4,
      metrics: { works_count: 98, citations: 12450, h_index: 55 },
      matched_topic: { topic_name: "Quantum Error Correction", topic_count: 19 },
      all_topics: [
        { topic_name: "Quantum Error Correction", count: 19, subfield: "Quantum Computing" },
        { topic_name: "Quantum Key Distribution", count: 24, subfield: "Quantum Cryptography" },
        { topic_name: "Entanglement Distillation", count: 16, subfield: "Quantum Information" },
        { topic_name: "Quantum Repeaters", count: 11, subfield: "Quantum Networks" },
        { topic_name: "Decoherence Mitigation", count: 9, subfield: "Quantum Computing" },
      ],
      why: [
        "19 publications match this research problem",
        "Exceptional h-index for career stage",
        "Interdisciplinary expertise across quantum domains",
        "Highly cited works on entanglement-based protocols",
      ],
      institution: "Stanford University",
      first_year: 2013,
      last_year: 2025,
      openalex_url: "https://openalex.org/A0003",
      orcid: "0000-0003-4567-8901",
      contacts: [
        { type: "email", value: "enakamura@stanford.edu", label: "Email", source: "ORCID" },
        { type: "url", value: "https://nakamura-quantum.stanford.edu", label: "Research Group", source: "ORCID" },
        { type: "url", value: "https://linkedin.com/in/emily-nakamura", label: "LinkedIn", source: "ORCID" },
      ],
    },
    {
      author_id: "A0004",
      author: "Prof. James Okafor",
      score: 76.8,
      metrics: { works_count: 115, citations: 7650, h_index: 38 },
      matched_topic: { topic_name: "Quantum Error Correction", topic_count: 15 },
      all_topics: [
        { topic_name: "Quantum Error Correction", count: 15, subfield: "Quantum Computing" },
        { topic_name: "Quantum Algorithms", count: 28, subfield: "Quantum Computing" },
        { topic_name: "Adiabatic Quantum Computing", count: 20, subfield: "Quantum Computing" },
        { topic_name: "Quantum Annealing", count: 17, subfield: "Quantum Computing" },
        { topic_name: "Optimization", count: 13, subfield: "Algorithms" },
      ],
      why: [
        "15 publications match this research problem",
        "Strong breadth across quantum computing subfields",
        "Consistent publication record over 12 years",
        "Leads a major quantum computing research group",
      ],
      institution: "University of Tokyo",
      first_year: 2012,
      last_year: 2025,
      openalex_url: "https://openalex.org/A0004",
      orcid: "0000-0004-5678-9012",
      contacts: [
        { type: "email", value: "okafor@tokyo.ac.jp", label: "Email", source: "ORCID" },
        { type: "url", value: "https://qclab.tokyo.ac.jp", label: "Lab Website", source: "ORCID" },
      ],
    },
    {
      author_id: "A0005",
      author: "Dr. Anna Kovalenko",
      score: 71.3,
      metrics: { works_count: 76, citations: 5430, h_index: 32 },
      matched_topic: { topic_name: "Quantum Error Correction", topic_count: 12 },
      all_topics: [
        { topic_name: "Quantum Error Correction", count: 12, subfield: "Quantum Computing" },
        { topic_name: "Quantum Machine Learning", count: 22, subfield: "Quantum AI" },
        { topic_name: "Variational Quantum Algorithms", count: 18, subfield: "Quantum Computing" },
        { topic_name: "Quantum Kernel Methods", count: 10, subfield: "Quantum AI" },
      ],
      why: [
        "12 publications match this research problem",
        "Rising star — rapid citation growth in last 3 years",
        "Unique intersection of error correction and quantum ML",
        "Active speaker at major quantum conferences",
      ],
      institution: "ETH Zurich",
      first_year: 2016,
      last_year: 2025,
      openalex_url: "https://openalex.org/A0005",
      orcid: "0000-0005-6789-0123",
      contacts: [
        { type: "email", value: "kovalenko@ethz.ch", label: "Email", source: "ORCID" },
      ],
    },
    {
      author_id: "A0006",
      author: "Prof. Rajesh Patel",
      score: 65.9,
      metrics: { works_count: 203, citations: 18200, h_index: 71 },
      matched_topic: { topic_name: "Quantum Error Correction", topic_count: 9 },
      all_topics: [
        { topic_name: "Quantum Error Correction", count: 9, subfield: "Quantum Computing" },
        { topic_name: "Quantum Information Theory", count: 42, subfield: "Information Theory" },
        { topic_name: "Entropy and Channel Capacity", count: 35, subfield: "Information Theory" },
        { topic_name: "Quantum Cryptography", count: 30, subfield: "Quantum Cryptography" },
        { topic_name: "Noisy Channels", count: 25, subfield: "Information Theory" },
        { topic_name: "Classical Quantum Interfaces", count: 18, subfield: "Quantum Computing" },
      ],
      why: [
        "9 publications match this research problem",
        "Very high h-index of 71 — top authority in broader field",
        "Extensive publication record with 200+ works",
        "Foundational contributions to quantum information theory",
      ],
      institution: "IISc Bangalore",
      first_year: 2003,
      last_year: 2025,
      openalex_url: "https://openalex.org/A0006",
      orcid: "0000-0006-7890-1234",
      contacts: [
        { type: "email", value: "rpatel@iisc.ac.in", label: "Email", source: "ORCID" },
        { type: "url", value: "https://linkedin.com/in/rajesh-patel-iisc", label: "LinkedIn", source: "ORCID" },
        { type: "url", value: "https://qpac.iisc.ac.in", label: "Research Group", source: "ORCID" },
      ],
    },
    {
      author_id: "A0007",
      author: "Dr. Lisa Bergström",
      score: 59.4,
      metrics: { works_count: 52, citations: 3210, h_index: 24 },
      matched_topic: { topic_name: "Quantum Error Correction", topic_count: 7 },
      all_topics: [
        { topic_name: "Quantum Error Correction", count: 7, subfield: "Quantum Computing" },
        { topic_name: "Quantum Dot Qubits", count: 18, subfield: "Quantum Hardware" },
        { topic_name: "Semiconductor Quantum Devices", count: 14, subfield: "Quantum Hardware" },
        { topic_name: "Spin Qubits", count: 11, subfield: "Quantum Hardware" },
      ],
      why: [
        "7 publications match this research problem",
        "Hands-on expertise in quantum hardware implementation",
        "Practical error correction for semiconductor qubits",
      ],
      institution: "KTH Royal Institute of Technology",
      first_year: 2017,
      last_year: 2025,
      openalex_url: "https://openalex.org/A0007",
      orcid: "0000-0007-8901-2345",
      contacts: [],
    },
    {
      author_id: "A0008",
      author: "Prof. Wei Zhang",
      score: 54.1,
      metrics: { works_count: 167, citations: 11300, h_index: 52 },
      matched_topic: { topic_name: "Quantum Error Correction", topic_count: 6 },
      all_topics: [
        { topic_name: "Quantum Error Correction", count: 6, subfield: "Quantum Computing" },
        { topic_name: "Superconducting Qubits", count: 38, subfield: "Quantum Hardware" },
        { topic_name: "Microwave Quantum Optics", count: 29, subfield: "Quantum Optics" },
        { topic_name: "Circuit QED", count: 25, subfield: "Quantum Hardware" },
        { topic_name: "Quantum Measurement", count: 20, subfield: "Quantum Information" },
      ],
      why: [
        "6 publications match this research problem",
        "World-leading expertise in superconducting qubit hardware",
        "Strong experimental background for implementing error correction",
      ],
      institution: "University of Science and Technology of China",
      first_year: 2009,
      last_year: 2025,
      openalex_url: "https://openalex.org/A0008",
      orcid: "0000-0008-9012-3456",
      contacts: [
        { type: "url", value: "https://quantum.ustc.edu.cn", label: "Lab Website", source: "ORCID" },
      ],
    },
    {
      author_id: "A0009",
      author: "Dr. Sophie Laurent",
      score: 49.7,
      metrics: { works_count: 41, citations: 2890, h_index: 21 },
      matched_topic: { topic_name: "Quantum Error Correction", topic_count: 5 },
      all_topics: [
        { topic_name: "Quantum Error Correction", count: 5, subfield: "Quantum Computing" },
        { topic_name: "Tensor Networks", count: 16, subfield: "Quantum Many-Body" },
        { topic_name: "Entanglement Entropy", count: 12, subfield: "Quantum Many-Body" },
        { topic_name: "Matrix Product States", count: 9, subfield: "Quantum Many-Body" },
      ],
      why: [
        "5 publications match this research problem",
        "Novel approach combining tensor networks with error correction",
        "Emerging contributor with growing citation trajectory",
      ],
      institution: "Université Paris-Saclay",
      first_year: 2018,
      last_year: 2025,
      openalex_url: "https://openalex.org/A0009",
      orcid: "0000-0009-0123-4567",
      contacts: [
        { type: "email", value: "sophie.laurent@universite-paris-saclay.fr", label: "Email", source: "ORCID" },
        { type: "url", value: "https://linkedin.com/in/sophie-laurent-quantum", label: "LinkedIn", source: "ORCID" },
      ],
    },
    {
      author_id: "A0010",
      author: "Dr. Kwame Mensah",
      score: 43.2,
      metrics: { works_count: 33, citations: 1870, h_index: 17 },
      matched_topic: { topic_name: "Quantum Error Correction", topic_count: 4 },
      all_topics: [
        { topic_name: "Quantum Error Correction", count: 4, subfield: "Quantum Computing" },
        { topic_name: "Quantum Chemistry", count: 14, subfield: "Quantum Applications" },
        { topic_name: "Variational Quantum Eigensolver", count: 11, subfield: "Quantum Applications" },
        { topic_name: "Molecular Simulation", count: 8, subfield: "Quantum Chemistry" },
      ],
      why: [
        "4 publications match this research problem",
        "Unique perspective on error correction for quantum chemistry",
        "Young researcher with promising publication trajectory",
      ],
      institution: "University of Cape Town",
      first_year: 2019,
      last_year: 2025,
      openalex_url: "https://openalex.org/A0010",
      orcid: "0000-0010-1234-5678",
      contacts: [],
    },
  ],
}

function useExample(q: string) {
  query.value = q
  search()
}

async function search() {
  const q = query.value.trim()
  if (!q) return

  loading.value = true
  error.value = null
  result.value = null
  selectedIndex.value = null
  // Use mock data immediately so the layout is visible
  const mock = JSON.parse(JSON.stringify(MOCK_RESULT))
  mock.query = q
  result.value = mock
  loading.value = false
  selectedIndex.value = 0
}

function selectExpert(index: number) {
  selectedIndex.value = index
}
</script>

<template>
  <div class="min-h-screen bg-white dark:bg-[#111] font-['Inter',system-ui,sans-serif]">
    <Navbar />

    <div class="max-w-[1280px] mx-auto px-4 md:px-8 pb-12">
      <!-- Header + Search -->
      <div class="pt-8 pb-6">
        <div class="mb-6">
          <h1 class="text-2xl md:text-[1.75rem] font-bold text-gray-900 dark:text-gray-100 m-0 mb-1.5">Research Expert Discovery</h1>
          <p class="text-sm md:text-base text-gray-500 dark:text-gray-400 m-0">
            Find top researchers and domain experts for any research problem.
          </p>
        </div>

        <!-- Search bar -->
        <div class="bg-white dark:bg-[#1c1c1c] border border-gray-200 dark:border-[#2a2a2a] rounded-xl p-5 md:p-6">
          <div class="flex flex-col md:flex-row gap-3">
            <input
              v-model="query"
              type="text"
              placeholder="Describe your research problem... e.g. 'quantum error correction'"
              class="flex-1 px-4 py-3 border-2 border-gray-200 dark:border-[#333] rounded-lg bg-white dark:bg-[#111] text-gray-900 dark:text-gray-100 text-sm md:text-base outline-none focus:border-blue-500 dark:focus:border-blue-400 transition-colors placeholder:text-gray-400 dark:placeholder:text-gray-500"
              @keyup.enter="search"
            />
            <button
              @click="search"
              :disabled="loading || !query.trim()"
              class="inline-flex items-center gap-1.5 px-6 py-3 bg-blue-500 hover:bg-blue-600 disabled:opacity-50 disabled:cursor-not-allowed text-white font-semibold text-sm rounded-lg transition-colors whitespace-nowrap"
            >
              <span v-if="loading" class="w-4 h-4 border-2 border-white/30 border-t-white rounded-full animate-spin"></span>
              <svg v-else class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M21 21l-6-6m2-5a7 7 0 11-14 0 7 7 0 0114 0z" />
              </svg>
              {{ loading ? "Searching..." : "Search" }}
            </button>
          </div>

          <!-- Example queries -->
          <div class="flex flex-wrap items-center gap-2 mt-4">
            <span class="text-sm text-gray-500 dark:text-gray-400">Try:</span>
            <button
              v-for="eq in exampleQueries"
              :key="eq"
              @click="useExample(eq)"
              class="px-3.5 py-1.5 text-xs md:text-sm bg-gray-50 dark:bg-[#222] text-gray-500 dark:text-gray-400 border border-gray-200 dark:border-[#333] rounded-full cursor-pointer hover:bg-blue-50 dark:hover:bg-blue-900/30 hover:text-blue-500 dark:hover:text-blue-400 hover:border-blue-500 dark:hover:border-blue-400 transition-all"
            >
              {{ eq }}
            </button>
          </div>
        </div>
      </div>

      <!-- Error -->
      <div v-if="error" class="flex items-center gap-2.5 px-5 py-3.5 mb-6 bg-red-50 dark:bg-red-900/20 border border-red-200 dark:border-red-800 rounded-lg text-red-700 dark:text-red-400 text-sm">
        <span>❌</span>
        <span>{{ error }}</span>
      </div>

      <!-- Loading skeleton -->
      <div v-if="loading" class="bg-white dark:bg-[#1c1c1c] border border-gray-200 dark:border-[#2a2a2a] rounded-xl p-6 flex flex-col gap-4">
        <div class="h-3.5 rounded bg-gray-200 dark:bg-[#333] animate-pulse w-3/5"></div>
        <div v-for="n in 4" :key="n" class="flex items-center gap-4">
          <div class="w-9 h-9 rounded-full bg-gray-200 dark:bg-[#333] animate-pulse"></div>
          <div class="flex-1 flex flex-col gap-2">
            <div class="h-3.5 rounded bg-gray-200 dark:bg-[#333] animate-pulse w-2/5"></div>
            <div class="h-3 rounded bg-gray-200 dark:bg-[#333] animate-pulse w-1/4"></div>
          </div>
        </div>
      </div>

      <!-- Results summary -->
      <!-- <div v-if="result && !loading" class="flex flex-col md:flex-row items-start md:items-center justify-between px-5 py-3.5 mb-6 bg-white dark:bg-[#1c1c1c] border border-gray-200 dark:border-[#2a2a2a] rounded-lg text-sm text-gray-500 dark:text-gray-400 gap-3">
        <div class="flex flex-col md:flex-row md:items-center gap-1.5 md:gap-3">
          <span>📄 <strong>{{ result.total_works_found }}</strong> papers found</span>
          <span class="hidden md:inline w-px h-4 bg-gray-200 dark:bg-[#333]"></span>
          <span>👥 <strong>{{ result.total_authors_extracted }}</strong> authors extracted</span>
          <span class="hidden md:inline w-px h-4 bg-gray-200 dark:bg-[#333]"></span>
          <span>🏆 <strong>{{ result.experts.length }}</strong> experts ranked</span>
        </div>
        <span class="italic text-gray-400 dark:text-gray-500 text-xs md:text-sm">"{{ result.query }}"</span>
      </div> -->

      <!-- Master-Detail Layout -->
      <div
        v-if="result && result.experts.length > 0 && !loading"
        class="flex flex-col md:flex-row border border-gray-200 dark:border-[#2a2a2a] rounded-xl overflow-hidden bg-white dark:bg-[#1c1c1c] md:min-h-[620px] md:max-h-[78vh]"
      >
        <!-- Left: Expert List -->
        <div class="w-full md:w-[420px] md:min-w-[360px] shrink-0 overflow-y-auto max-h-[50vh] md:max-h-none border-b md:border-b-0 md:border-r border-gray-200 dark:border-[#2a2a2a]">
          <ExpertList
            :experts="result.experts"
            :selectedIndex="selectedIndex"
            @select="selectExpert"
          />
        </div>

        <!-- Right: Expert Details -->
        <div class="flex-1 min-w-0 overflow-y-auto">
          <ExpertDetailsPanel :expert="selectedExpert" />
        </div>
      </div>

      <!-- Empty state -->
      <div
        v-if="result && result.experts.length === 0 && !loading"
        class="text-center py-16 px-6 bg-white dark:bg-[#1c1c1c] border border-gray-200 dark:border-[#2a2a2a] rounded-xl"
      >
        <div class="text-5xl mb-3">🔍</div>
        <h3 class="text-lg font-semibold text-gray-900 dark:text-gray-100 mb-1.5">No experts found</h3>
        <p class="text-sm text-gray-500 dark:text-gray-400 max-w-[420px] mx-auto">
          {{ result.total_works_found > 0
            ? "Authors were extracted but none matched your query after validation."
            : "No research papers were found for this query. Try a different search term." }}
        </p>
      </div>
    </div>
  </div>
</template>

<style>
/* Thin light-grey scrollbar */
::-webkit-scrollbar {
  width: 5px;
  height: 5px;
}
::-webkit-scrollbar-track {
  background: transparent;
}
::-webkit-scrollbar-thumb {
  background: #d1d5db;
  border-radius: 99px;
}
::-webkit-scrollbar-thumb:hover {
  background: #9ca3af;
}
@media (prefers-color-scheme: dark) {
  ::-webkit-scrollbar-thumb {
    background: #444;
  }
  ::-webkit-scrollbar-thumb:hover {
    background: #666;
  }
}
</style>
