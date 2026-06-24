<script setup lang="ts">
definePageMeta({
  middleware: "auth",
})

import { ref, computed } from "vue"
import { useExpertDiscovery, type DiscoverExpertsResponse } from "~/composables/useExpertDiscovery"

const { discoverExperts } = useExpertDiscovery()

const query = ref("")
const loading = ref(false)
const error = ref<string | null>(null)
const result = ref<DiscoverExpertsResponse | null>(null)
const rawJson = ref<string>("")
const activeTab = ref<"experts" | "inventors" | "json">("experts")

// ── Group raw documents by inventor ───────────
const inventorGroups = computed(() => {
  if (!result.value?.raw_documents) return []

  const groups: { name: string; patents: { id: string; title: string }[] }[] = []
  const map = new Map<string, { id: string; title: string }[]>()

  for (const doc of result.value.raw_documents) {
    const source = doc._source || {}
    const inventors: string[] = source.inventors || []
    const docId = doc._id || ""
    const title = source.title || "Untitled"

    for (const inv of inventors) {
      if (!map.has(inv)) map.set(inv, [])
      map.get(inv)!.push({ id: docId, title })
    }
  }

  for (const [name, patents] of map.entries()) {
    groups.push({ name, patents })
  }

  groups.sort((a, b) => b.patents.length - a.patents.length)
  return groups
})

async function search() {
  const q = query.value.trim()
  if (!q) return

  loading.value = true
  error.value = null
  result.value = null
  rawJson.value = ""

  try {
    const data = await discoverExperts(q, 10)
    result.value = data
    rawJson.value = JSON.stringify(data, null, 2)
  } catch (err: any) {
    error.value = err?.response?.data?.detail || err.message || "Failed to discover experts"
  } finally {
    loading.value = false
  }
}

function getScoreColor(score: number): string {
  if (score >= 0.7) return "text-green-600 bg-green-50 border-green-200"
  if (score >= 0.4) return "text-yellow-600 bg-yellow-50 border-yellow-200"
  return "text-red-600 bg-red-50 border-red-200"
}

function getRoleBadge(role: string): string {
  const badges: Record<string, string> = {
    inventor: "bg-purple-100 text-purple-800",
    author: "bg-blue-100 text-blue-800",
    applicant: "bg-amber-100 text-amber-800",
    assignee: "bg-gray-100 text-gray-800",
  }
  return badges[role.toLowerCase()] || "bg-gray-100 text-gray-800"
}

function getScoreBarWidth(score: number): string {
  return `${Math.round(score * 100)}%`
}
</script>

<template>
  <div class="min-h-screen bg-gradient-to-br from-slate-50 via-white to-blue-50">
    <Navbar />

    <!-- Header -->
    <div class="border-b border-gray-200 bg-white/80 backdrop-blur-sm">
      <div class="max-w-7xl mx-auto px-4 sm:px-6 py-4">
        <div class="flex items-center justify-between">
          <div>
            <h1 class="text-xl font-bold text-gray-900 flex items-center gap-2">
              <span>🔬</span>
              Expert Discovery
            </h1>
            <p class="text-sm text-gray-500">
              Find top inventors and researchers from patent data
            </p>
          </div>
        </div>
      </div>
    </div>

    <!-- Search Section -->
    <div class="max-w-7xl mx-auto px-4 sm:px-6 py-6">
      <div class="bg-white rounded-xl shadow-md border border-gray-200 p-6">
        <form @submit.prevent="search" class="flex gap-3">
          <input
            v-model="query"
            type="text"
            placeholder="e.g. Find experts in lithium battery cathode materials"
            class="flex-1 px-4 py-3 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent text-gray-900 placeholder-gray-400"
            :disabled="loading"
          />
          <button
            type="submit"
            :disabled="loading || !query.trim()"
            class="px-6 py-3 bg-blue-600 hover:bg-blue-700 disabled:bg-blue-300 text-white font-semibold rounded-lg transition duration-200 flex items-center gap-2"
          >
            <span v-if="loading" class="inline-block w-4 h-4 border-2 border-white border-t-transparent rounded-full animate-spin"></span>
            <span v-else>🔍</span>
            {{ loading ? "Searching..." : "Discover Experts" }}
          </button>
        </form>

        <!-- Error -->
        <div
          v-if="error"
          class="mt-4 p-4 bg-red-50 border border-red-200 rounded-lg text-red-700 text-sm"
        >
          {{ error }}
        </div>
      </div>
    </div>

    <!-- Results Section -->
    <div v-if="result" class="max-w-7xl mx-auto px-4 sm:px-6 pb-12">
      <!-- Summary bar -->
      <div class="bg-white rounded-xl shadow-sm border border-gray-200 p-4 mb-4 flex items-center justify-between">
        <div class="text-sm text-gray-600">
          <span class="font-semibold text-gray-900">{{ result.total_documents_found }}</span> patents analyzed
          <span v-if="result.xsearch_id" class="ml-3 text-xs text-gray-400">
            Session: <code class="bg-gray-100 px-1.5 py-0.5 rounded">{{ result.xsearch_id }}</code>
          </span>
        </div>
        <div class="text-sm text-gray-600">
          <span class="font-semibold text-gray-900">{{ result.experts.length }}</span> experts found for
          <span class="italic text-gray-900">"{{ result.query }}"</span>
        </div>
      </div>

      <!-- View tabs (mobile+desktop) -->
      <div class="mb-4 flex gap-2">
        <button
          @click="activeTab = 'experts'"
          class="px-4 py-2 text-sm font-medium rounded-lg transition"
          :class="activeTab === 'experts' ? 'bg-blue-600 text-white shadow-md' : 'bg-white text-gray-600 border border-gray-300 hover:bg-gray-50'"
        >
          🏆 Experts
        </button>
        <button
          @click="activeTab = 'inventors'"
          class="px-4 py-2 text-sm font-medium rounded-lg transition"
          :class="activeTab === 'inventors' ? 'bg-blue-600 text-white shadow-md' : 'bg-white text-gray-600 border border-gray-300 hover:bg-gray-50'"
        >
          👥 Inventors
        </button>
        <button
          @click="activeTab = 'json'"
          class="px-4 py-2 text-sm font-medium rounded-lg transition"
          :class="activeTab === 'json' ? 'bg-blue-600 text-white shadow-md' : 'bg-white text-gray-600 border border-gray-300 hover:bg-gray-50'"
        >
          📋 JSON
        </button>
      </div>

      <!-- Content: Experts view -->
      <div v-show="activeTab === 'experts'">
        <div v-if="result.experts.length === 0" class="bg-white rounded-xl shadow-sm border border-gray-200 p-8 text-center">
          <div class="text-4xl mb-3">🔬</div>
          <h3 class="text-lg font-semibold text-gray-900 mb-1">No Experts Found</h3>
          <p class="text-gray-500 text-sm">No inventor or researcher profiles could be extracted. Try a different search query.</p>
        </div>

        <div class="space-y-4">
          <div
            v-for="expert in result.experts"
            :key="expert.rank"
            class="bg-white rounded-xl shadow-sm border border-gray-200 overflow-hidden hover:shadow-md transition"
          >
            <div class="p-5 pb-3 flex items-start justify-between gap-4">
              <div class="flex items-start gap-4">
                <div
                  class="w-10 h-10 rounded-full flex items-center justify-center text-sm font-bold shrink-0"
                  :class="{
                    'bg-yellow-100 text-yellow-800 border-2 border-yellow-400': expert.rank === 1,
                    'bg-gray-100 text-gray-700 border-2 border-gray-300': expert.rank === 2,
                    'bg-amber-50 text-amber-700 border-2 border-amber-300': expert.rank === 3,
                    'bg-slate-50 text-slate-600 border border-slate-300': expert.rank > 3,
                  }"
                >
                  #{{ expert.rank }}
                </div>
                <div>
                  <h3 class="text-lg font-bold text-gray-900">{{ expert.name }}</h3>
                  <div v-if="expert.contact?.organization" class="flex flex-wrap gap-2 mt-1">
                    <span class="text-xs text-gray-500 flex items-center gap-1">🏢 {{ expert.contact.organization }}</span>
                  </div>
                </div>
              </div>
              <div class="shrink-0 px-3 py-1.5 rounded-lg border font-bold text-sm" :class="getScoreColor(expert.score)">
                {{ (expert.score * 100).toFixed(1) }}%
              </div>
            </div>
            <div class="px-5 pb-2">
              <div class="w-full bg-gray-100 rounded-full h-1.5">
                <div
                  class="h-1.5 rounded-full transition-all duration-500"
                  :class="{ 'bg-green-500': expert.score >= 0.7, 'bg-yellow-500': expert.score >= 0.4 && expert.score < 0.7, 'bg-red-500': expert.score < 0.4 }"
                  :style="{ width: getScoreBarWidth(expert.score) }"
                ></div>
              </div>
            </div>
            <div class="px-5 pb-2">
              <div class="flex flex-wrap gap-1.5">
                <span v-for="skill in expert.expertise" :key="skill" class="px-2 py-0.5 bg-blue-50 text-blue-700 text-xs rounded-full border border-blue-100">{{ skill }}</span>
              </div>
            </div>
            <div class="px-5 pb-2">
              <details class="group">
                <summary class="text-xs text-gray-500 cursor-pointer hover:text-gray-700 select-none">📊 Ranking reasoning</summary>
                <p class="mt-1 text-sm text-gray-600 leading-relaxed bg-gray-50 rounded-lg p-3">{{ expert.reasoning }}</p>
              </details>
            </div>
            <div v-if="expert.evidence.length > 0" class="border-t border-gray-100 bg-gray-50/50">
              <details class="group" :open="expert.rank <= 3">
                <summary class="px-5 py-2.5 text-xs text-gray-500 cursor-pointer hover:text-gray-700 select-none flex items-center gap-1">
                  <span>📄 Evidence ({{ expert.evidence.length }} documents)</span>
                </summary>
                <div class="px-5 pb-3 space-y-1.5">
                  <div v-for="ev in expert.evidence" :key="ev.patent_id" class="flex items-center gap-2 text-sm">
                    <span class="px-1.5 py-0.5 rounded text-[10px] font-medium uppercase" :class="getRoleBadge(ev.role)">{{ ev.role }}</span>
                    <span class="text-gray-700 truncate">{{ ev.title || ev.patent_id }}</span>
                    <code class="text-[10px] text-gray-400 shrink-0">{{ ev.patent_id }}</code>
                  </div>
                </div>
              </details>
            </div>
          </div>
        </div>
      </div>

      <!-- Content: Inventors view (raw data grouped) -->
      <div v-show="activeTab === 'inventors'">
        <div v-if="inventorGroups.length === 0" class="bg-white rounded-xl shadow-sm border border-gray-200 p-8 text-center">
          <div class="text-4xl mb-3">👥</div>
          <h3 class="text-lg font-semibold text-gray-900 mb-1">No Inventors Found</h3>
          <p class="text-gray-500 text-sm">No inventor data could be extracted from the patent documents. Try a different search query.</p>
        </div>

        <div class="space-y-4">
          <div v-for="group in inventorGroups" :key="group.name" class="bg-white rounded-xl shadow-sm border border-gray-200 overflow-hidden hover:shadow-md transition">
            <div class="p-5 pb-3 flex items-center justify-between gap-4">
              <div class="flex items-center gap-3">
                <div class="w-10 h-10 rounded-full bg-purple-100 text-purple-800 flex items-center justify-center text-lg font-bold shrink-0">
                  {{ group.name.charAt(0) }}
                </div>
                <div>
                  <h3 class="text-lg font-bold text-gray-900">{{ group.name }}</h3>
                  <p class="text-xs text-gray-500">{{ group.patents.length }} patent{{ group.patents.length !== 1 ? 's' : '' }}</p>
                </div>
              </div>
              <span class="text-xs text-gray-400 font-mono">{{ group.patents.length }} docs</span>
            </div>
            <div class="border-t border-gray-100">
              <div v-for="patent in group.patents" :key="patent.id" class="px-5 py-3 border-b border-gray-50 last:border-b-0 hover:bg-gray-50/50 transition">
                <div class="flex items-start gap-2">
                  <span class="text-gray-400 mt-0.5 shrink-0">📄</span>
                  <div class="min-w-0">
                    <p class="text-sm text-gray-800 leading-snug">{{ patent.title }}</p>
                    <code class="text-[11px] text-gray-400 mt-0.5 block">{{ patent.id }}</code>
                  </div>
                </div>
              </div>
            </div>
          </div>
        </div>
      </div>

      <!-- Content: Raw JSON -->
      <div v-show="activeTab === 'json'">
        <div class="bg-gray-900 rounded-xl shadow-sm border border-gray-700">
          <div class="px-4 py-3 border-b border-gray-700 flex items-center justify-between">
            <span class="text-xs text-gray-400 font-mono">response.json</span>
            <span class="text-[10px] text-gray-500">{{ rawJson.length.toLocaleString() }} bytes</span>
          </div>
          <pre class="p-4 overflow-auto text-xs leading-relaxed text-green-400 font-mono max-h-[80vh]" style="scrollbar-width: thin;"><code>{{ rawJson }}</code></pre>
        </div>
      </div>
    </div>
  </div>
</template>
