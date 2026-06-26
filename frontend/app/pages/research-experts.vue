<script setup lang="ts">
definePageMeta({
  middleware: "auth",
})

import { ref, computed } from "vue"
import { useResearchExpert, type ResearchExpertResponse } from "~/composables/useResearchExpert"

const { searchExperts } = useResearchExpert()

const query = ref("")
const loading = ref(false)
const error = ref<string | null>(null)
const result = ref<ResearchExpertResponse | null>(null)
const showDetails = ref<number | null>(null)

const exampleQueries = [
  "quantum error correction",
  "lithium battery thermal management",
  "carbon nanotube interconnects",
  "deep learning for medical imaging",
]

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
  showDetails.value = null

  //search with user query and return all experts ranked by relevance
  try {
    const data = await searchExperts(q)
    result.value = data
  } catch (err: any) {
    error.value = err?.response?.data?.detail || err.message || "Failed to search experts"
  } finally {
    loading.value = false
  }
}

function toggleDetails(index: number) {
  showDetails.value = showDetails.value === index ? null : index
}
</script>

<template>
<div class="min-h-screen bg-gradient-to-br from-slate-50 to-slate-100">
  <Navbar />

  <div class="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-12">
    <!-- Header -->
    <div class="mb-8">
      <h1 class="text-4xl font-bold text-gray-900 mb-2">🔬 Research Expert Discovery</h1>
      <p class="text-gray-600">
        Find top researchers and domain experts for any research problem.
      </p>
    </div>

    <!-- Search Bar -->
    <div class="bg-white rounded-lg shadow-md border border-gray-200 p-6 mb-8">
      <div class="flex gap-3">
        <input
          v-model="query"
          type="text"
          placeholder="Describe your research problem... e.g. 'quantum error correction'"
          class="flex-1 px-4 py-3 border-2 border-gray-200 rounded-lg focus:border-blue-500 focus:ring-2 focus:ring-blue-200 outline-none text-lg transition"
          @keyup.enter="search"
        />
        <button
          @click="search"
          :disabled="loading || !query.trim()"
          class="px-8 py-3 bg-blue-600 hover:bg-blue-700 disabled:bg-gray-400 text-white font-semibold rounded-lg transition duration-200 flex items-center gap-2"
        >
          <span v-if="loading" class="inline-block animate-spin">⏳</span>
          <span v-else>🔍</span>
          {{ loading ? "Searching..." : "Search Experts" }}
        </button>
      </div>

      <!-- Example queries -->
      <div class="mt-4 flex flex-wrap gap-2">
        <span class="text-sm text-gray-500 mr-1">Try:</span>
        <button
          v-for="eq in exampleQueries"
          :key="eq"
          @click="useExample(eq)"
          class="px-3 py-1 text-sm bg-gray-100 hover:bg-blue-100 text-gray-600 hover:text-blue-700 rounded-full transition"
        >
          {{ eq }}
        </button>
      </div>
    </div>

    <!-- Error -->
    <div v-if="error" class="bg-red-50 border-2 border-red-200 rounded-lg p-4 mb-8">
      <p class="text-red-700 font-medium">❌ {{ error }}</p>
    </div>

    <!-- Results Summary -->
    <div v-if="result" class="bg-white rounded-lg shadow-md border border-gray-200 p-4 mb-6">
      <div class="flex items-center justify-between text-sm text-gray-600">
        <div class="flex gap-6">
          <span>📄 <strong>{{ result.total_works_found }}</strong> papers found</span>
          <span>👥 <strong>{{ result.total_authors_extracted }}</strong> authors extracted</span>
          <span>🏆 <strong>{{ result.experts.length }}</strong> experts ranked</span>
        </div>
        <span class="text-gray-400 italic">Query: "{{ result.query }}"</span>
      </div>
    </div>

    <!-- Loading Skeleton -->
    <div v-if="loading" class="space-y-4">
      <div v-for="n in 3" :key="n" class="bg-white rounded-lg shadow-md border border-gray-200 p-6 animate-pulse">
        <div class="h-6 bg-gray-200 rounded w-1/3 mb-3"></div>
        <div class="h-4 bg-gray-200 rounded w-2/3 mb-2"></div>
        <div class="h-4 bg-gray-200 rounded w-1/2"></div>
      </div>
    </div>

    <!-- Expert Cards -->
    <div v-if="result && result.experts.length > 0" class="space-y-4">
      <div
        v-for="(expert, index) in result.experts"
        :key="expert.author_id"
        class="bg-white rounded-lg shadow-md border border-gray-200 overflow-hidden hover:shadow-lg transition duration-200"
      >
        <!-- Card Header -->
        <div
          class="p-6 cursor-pointer"
          @click="toggleDetails(index)"
        >
          <div class="flex items-start justify-between">
            <div class="flex-1">
              <div class="flex items-center gap-3 mb-2">
                <span class="text-2xl">🥇</span>
                <h3 class="text-xl font-bold text-gray-900">{{ expert.author }}</h3>
                <span
                  v-if="expert.institution"
                  class="px-2 py-0.5 text-xs font-medium bg-blue-100 text-blue-800 rounded-full"
                >
                  {{ expert.institution }}
                </span>
                <!-- <a
                  v-if="expert.openalex_url"
                  :href="expert.openalex_url"
                  target="_blank"
                  rel="noopener noreferrer"
                  class="inline-flex items-center gap-1 px-2.5 py-1 text-xs font-medium text-purple-700 bg-purple-50 hover:bg-purple-100 rounded-full transition border border-purple-200"
                  title="View on OpenAlex"
                  @click.stop
                >
                  <svg class="w-3.5 h-3.5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M10 6H6a2 2 0 00-2 2v10a2 2 0 002 2h10a2 2 0 002-2v-4M14 4h6m0 0v6m0-6L10 14" />
                  </svg>
                  OpenAlex
                </a> -->
              </div>

              <!-- <div class="flex items-center gap-2 mb-3">
                <span
                  class="px-3 py-1 text-sm font-bold rounded-lg border"
                  :class="getScoreColor(expert.score)"
                >
                  Score: {{ expert.score.toFixed(1) }}
                </span>
                <span class="text-sm text-gray-500">
                  h-index: {{ expert.metrics.h_index }}
                </span>
                <span class="text-sm text-gray-500">·</span>
                <span class="text-sm text-gray-500">
                  {{ expert.metrics.works_count }} works
                </span>
                <span v-if="expert.first_year" class="text-sm text-gray-500">·</span>
                <span v-if="expert.first_year" class="text-sm text-gray-500">
                  📅 {{ expert.first_year }} – {{ expert.last_year || "present" }}
                </span>
              </div> -->

              <!-- Matched Topic -->
              <!-- <div v-if="expert.matched_topic" class="mb-2">
                <span class="text-sm font-medium text-green-700">
                  🎯 Matched: {{ expert.matched_topic.topic_name }}
                  ({{ expert.matched_topic.topic_count }} works)
                </span>
              </div> -->

              <!-- Why (Reasoning) — skip "Ranked #..." lines -->
              <div class="space-y-1">
                <template v-for="(reason, ri) in expert.why" :key="ri">
                  <p
                    v-if="!reason.startsWith('Ranked')"
                    class="text-sm text-gray-600 flex items-start gap-2"
                  >
                    <span class="text-blue-500 mt-0.5">•</span>
                    {{ reason }}
                  </p>
                </template>
              </div>
            </div>

            <div class="text-gray-400 text-sm ml-4">
              {{ showDetails === index ? "▲ Hide" : "▼ Details" }}
            </div>
          </div>
        </div>

        <!-- Expanded Details -->
        <div v-if="showDetails === index" class="border-t border-gray-200 bg-gray-50 p-6">
          <div class="grid grid-cols-1 md:grid-cols-2 gap-6">
            <!-- Metrics -->
            <div>
              <h4 class="font-semibold text-gray-900 mb-3">📊 Metrics</h4>
              <a
                v-if="expert.openalex_url"
                :href="expert.openalex_url"
                target="_blank"
                rel="noopener noreferrer"
                class="inline-flex items-center gap-1.5 mb-4 px-3 py-1.5 text-sm font-medium text-purple-700 bg-purple-50 hover:bg-purple-100 rounded-lg transition border border-purple-200"
              >
                <svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M10 6H6a2 2 0 00-2 2v10a2 2 0 002 2h10a2 2 0 002-2v-4M14 4h6m0 0v6m0-6L10 14" />
                </svg>
                View OpenAlex Profile ↗
              </a>
              <div class="space-y-2">
                <div class="flex justify-between text-sm">
                  <span class="text-gray-600">Works Count</span>
                  <span class="font-medium">{{ expert.metrics.works_count }}</span>
                </div>
                <div class="flex justify-between text-sm">
                  <span class="text-gray-600">Total Citations</span>
                  <span class="font-medium">{{ expert.metrics.citations }}</span>
                </div>
                <div class="flex justify-between text-sm">
                  <span class="text-gray-600">h-index</span>
                  <span class="font-medium">{{ expert.metrics.h_index }}</span>
                </div>
                <div class="flex justify-between text-sm">
                  <span class="text-gray-600">Research Years</span>
                  <span class="font-medium">{{ expert.first_year }} – {{ expert.last_year }}</span>
                </div>
              </div>
            </div>

            <!-- All Topics -->
            <div>
              <h4 class="font-semibold text-gray-900 mb-3">📚 Research Topics</h4>
              <div v-if="expert.all_topics.length > 0" class="space-y-2">
                <div
                  v-for="topic in expert.all_topics"
                  :key="topic.topic_name"
                  class="flex justify-between text-sm"
                >
                  <div>
                    <span class="text-gray-800 font-medium">{{ topic.topic_name }}</span>
                    <span v-if="topic.subfield" class="text-gray-400 text-xs ml-1">
                      ({{ topic.subfield }})
                    </span>
                  </div>
                  <span class="font-medium text-gray-600">{{ topic.count }} works</span>
                </div>
              </div>
              <p v-else class="text-sm text-gray-400">No topics available</p>
            </div>
          </div>

          <!-- Full Reasoning -->
          <div v-if="expert.why.length > 3" class="mt-4 pt-4 border-t border-gray-200">
            <h4 class="font-semibold text-gray-900 mb-2">💡 Full Reasoning</h4>
            <ul class="space-y-1">
              <template v-for="(reason, ri) in expert.why" :key="ri">
                <li
                  v-if="!reason.startsWith('Ranked')"
                  class="text-sm text-gray-600 flex items-start gap-2"
                >
                  <span class="text-blue-500 mt-0.5">•</span>
                  {{ reason }}
                </li>
              </template>
            </ul>
          </div>
        </div>
      </div>
    </div>

    <!-- Empty State -->
    <div
      v-if="result && result.experts.length === 0 && !loading"
      class="bg-white rounded-lg shadow-md border border-gray-200 p-12 text-center"
    >
      <div class="text-6xl mb-4">🔍</div>
      <h3 class="text-xl font-semibold text-gray-900 mb-2">No experts found</h3>
      <p class="text-gray-600">
        {{ result.total_works_found > 0
          ? `${result.total_authors_extracted} authors were extracted but none matched your query after LLM validation.`
          : "No research papers were found for this query. Try a different search term." }}
      </p>
    </div>
  </div>
</div>
</template>
