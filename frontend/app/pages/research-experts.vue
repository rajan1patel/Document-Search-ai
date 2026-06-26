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
  // No auto-load — user must click Search or an example query
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

  try {
    const data = await searchExperts(q, 20)
    result.value = data
  } catch (e: any) {
    error.value = e?.response?.data?.detail || e?.message || "Search failed. Please try again."
  } finally {
    loading.value = false
  }
}

function selectExpert(index: number) {
  selectedIndex.value = index
}
</script>

<template>
  <div class="min-h-screen bg-white font-['Inter',system-ui,sans-serif]">
    <Navbar />

    <div class="max-w-[1280px] mx-auto px-4 md:px-8 pb-12">
      <!-- Header + Search -->
      <div class="pt-8 pb-6">
        <div class="mb-6">
          <h1 class="text-2xl md:text-[1.75rem] font-bold text-[#111827] m-0 mb-1.5">Research Expert Discovery</h1>
          <p class="text-sm md:text-base text-[#6b7280] m-0">
            Find top researchers and domain experts for any research problem.
          </p>
        </div>

        <!-- Search bar -->
        <div class="bg-white border border-[#e5e7eb] rounded-xl p-5 md:p-6">
          <div class="flex flex-col md:flex-row gap-3">
            <input
              v-model="query"
              type="text"
              placeholder="Describe your research problem... e.g. 'quantum error correction'"
              class="flex-1 px-4 py-3 border-2 border-[#e5e7eb] rounded-lg bg-white text-[#111827] text-sm md:text-base outline-none focus:border-[#2563eb] transition-colors placeholder:text-[#9ca3af]"
              @keyup.enter="search"
            />
            <button
              @click="search"
              :disabled="loading || !query.trim()"
              class="inline-flex items-center gap-1.5 px-6 py-3 bg-[#2563eb] hover:bg-[#1d4ed8] disabled:opacity-50 disabled:cursor-not-allowed text-white font-semibold text-sm rounded-lg transition-colors whitespace-nowrap"
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
            <span class="text-sm text-[#6b7280]">Try:</span>
            <button
              v-for="eq in exampleQueries"
              :key="eq"
              @click="useExample(eq)"
              class="px-3.5 py-1.5 text-xs md:text-sm bg-[#f8fafc] text-[#6b7280] border border-[#e5e7eb] rounded-full cursor-pointer hover:bg-[#eff6ff] hover:text-[#2563eb] hover:border-[#2563eb] transition-all"
            >
              {{ eq }}
            </button>
          </div>
        </div>
      </div>

      <!-- Error -->
      <div v-if="error" class="flex items-center gap-2.5 px-5 py-3.5 mb-6 bg-[#fef2f2] border border-[#fecaca] rounded-lg text-[#b91c1c] text-sm">
        <span>{{ error }}</span>
      </div>

      <!-- Loading skeleton -->
      <div v-if="loading" class="bg-white border border-[#e5e7eb] rounded-xl p-6 flex flex-col gap-4">
        <div class="h-3.5 rounded bg-[#f3f4f6] animate-pulse w-3/5"></div>
        <div v-for="n in 4" :key="n" class="flex items-center gap-4">
          <div class="w-9 h-9 rounded-full bg-[#f3f4f6] animate-pulse"></div>
          <div class="flex-1 flex flex-col gap-2">
            <div class="h-3.5 rounded bg-[#f3f4f6] animate-pulse w-2/5"></div>
            <div class="h-3 rounded bg-[#f3f4f6] animate-pulse w-1/4"></div>
          </div>
        </div>
      </div>

      <!-- Master-Detail Layout -->
      <div
        v-if="result && result.experts.length > 0 && !loading"
        class="flex flex-col md:flex-row border border-[#e5e7eb] rounded-xl overflow-hidden bg-white md:min-h-[620px] md:max-h-[78vh]"
      >
        <!-- Left: Expert List -->
        <div
          :class="[
            selectedExpert
              ? 'w-full md:w-[420px] md:min-w-[360px] shrink-0 border-b md:border-b-0 md:border-r'
              : 'w-full',
            'overflow-y-auto max-h-[50vh] md:max-h-none border-[#e5e7eb]'
          ]"
        >
          <ExpertList
            :experts="result.experts"
            :selectedIndex="selectedIndex"
            @select="selectExpert"
          />
        </div>

        <!-- Right: Expert Details (hidden until an expert is selected) -->
        <div v-if="selectedExpert" class="flex-1 min-w-0 overflow-y-auto">
          <ExpertDetailsPanel :expert="selectedExpert" @close="selectedIndex = null" />
        </div>
      </div>

      <!-- Empty state -->
      <div
        v-if="result && result.experts.length === 0 && !loading"
        class="text-center py-16 px-6 bg-white border border-[#e5e7eb] rounded-xl"
      >
        <h3 class="text-lg font-semibold text-[#111827] mb-1.5">No experts found</h3>
        <p class="text-sm text-[#6b7280] max-w-[420px] mx-auto">
          {{ result.total_works_found > 0
            ? "Authors were extracted but none matched your query after validation."
            : "No research papers were found for this query. Try a different search term." }}
        </p>
      </div>
    </div>
  </div>
</template>

<style>
/* Thin scrollbar */
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
</style>
