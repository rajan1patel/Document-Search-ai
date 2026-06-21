<script setup lang="ts">
import { ref } from "vue"
import { useSearch } from "~/composables/useSearch"

interface SearchResult {
  filename: string | null
  page: number
  chunk: string
  score: number
}

const query = ref("")
const results = ref<SearchResult[]>([])
const loading = ref(false)
const error = ref<string | null>(null)

const { search } = useSearch()

async function runSearch() {
  if (!query.value) {
    error.value = "Please enter a search query"
    return
  }

  loading.value = true
  error.value = null

  try {
    results.value = await search(query.value)
  } catch (err: any) {
    error.value = err.message || "Search failed"
  } finally {
    loading.value = false
  }
}
</script>

<template>
<div class="space-y-6">
  <div class="flex gap-3">
    <input
      v-model="query"
      placeholder="Search documents..."
      @keyup.enter="runSearch"
      class="flex-1 px-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-600 focus:border-transparent outline-none transition"
    />

    <button
      @click="runSearch"
      :disabled="loading"
      class="bg-blue-600 hover:bg-blue-700 disabled:bg-gray-400 text-white font-semibold py-3 px-6 rounded-lg transition duration-200 disabled:cursor-not-allowed whitespace-nowrap"
    >
      {{ loading ? "Searching..." : "Search" }}
    </button>
  </div>

  <div v-if="error" class="bg-red-50 border border-red-200 rounded-lg p-4">
    <p class="text-red-800 font-medium">{{ error }}</p>
  </div>

  <div v-if="loading" class="text-center py-12">
    <p class="text-gray-600 text-lg">Searching your documents...</p>
  </div>

  <div v-else-if="results.length === 0 && query" class="text-center py-12">
    <p class="text-gray-600 text-lg">No results found</p>
  </div>

  <div v-else class="space-y-4">
    <div
      v-for="item in results"
      :key="`${item.filename}-${item.page}-${item.score}`"
      class="bg-gradient-to-r from-blue-50 to-purple-50 border border-gray-200 rounded-lg p-6 hover:shadow-md transition duration-200"
    >
      <div class="flex items-start justify-between mb-3">
        <div>
          <p class="text-sm text-gray-600 font-medium">Document ID</p>
          <h3 class="text-lg font-semibold text-gray-900">{{ item.filename || "Unknown document" }}</h3>
          <p class="text-sm text-gray-500">Page {{ item.page }}</p>
        </div>
        <div class="text-right">
          <p class="text-sm text-gray-600 font-medium">Relevance Score</p>
          <div class="flex items-center gap-2">
            <div class="w-24 h-2 bg-gray-200 rounded-full overflow-hidden">
              <div
                class="h-full bg-blue-600 transition-all"
                :style="{ width: `${Math.min(item.score * 100, 100)}%` }"
              ></div>
            </div>
            <span class="text-lg font-semibold text-blue-600">{{ (item.score * 100).toFixed(1) }}%</span>
          </div>
        </div>
      </div>

      <p class="text-gray-700 leading-relaxed">{{ item.chunk }}</p>
    </div>
  </div>
</div>
</template>
