<script setup lang="ts">
import { ref, computed } from "vue"
import type { ResearchExpertOutput } from "~/composables/useResearchExpert"

const props = defineProps<{
  expert: ResearchExpertOutput | null
}>()

const emit = defineEmits<{
  close: []
}>()

const topicsOpen = ref(false)
const papersOpen = ref(false)

const maxTopicCount = computed(() => {
  if (!props.expert) return 0
  return Math.max(...props.expert.all_topics.map(t => t.count), 1)
})

function formatNumber(n: number): string {
  if (n >= 1000) return (n / 1000).toFixed(1).replace(/\.0$/, "") + "k"
  return String(n)
}

// ── Mock papers (UI demo) ──────────────────────────────────
interface MockPaper {
  title: string
  year: number
  venue: string
  matched: boolean
}

const mockPapers = computed<MockPaper[]>(() => {
  if (!props.expert) return []
  const name = props.expert.author
  const seed = props.expert.author_id.charCodeAt(props.expert.author_id.length - 1)
  const papers: MockPaper[] = [
    {
      title: `Advances in ${props.expert.all_topics[0]?.topic_name || "Quantum Computing"}`,
      year: 2024 - (seed % 3),
      venue: "Nature Physics",
      matched: true,
    },
    {
      title: `${props.expert.all_topics[1]?.topic_name || "Quantum Information"}: A Comprehensive Study`,
      year: 2023 - (seed % 2),
      venue: "Physical Review Letters",
      matched: true,
    },
    {
      title: `Novel Approaches to ${props.expert.all_topics[2]?.topic_name || "Quantum Theory"}`,
      year: 2022 - (seed % 4),
      venue: "Quantum Science and Technology",
      matched: false,
    },
    {
      title: `Scalable Methods in ${props.expert.all_topics[0]?.subfield || "Quantum Physics"}`,
      year: 2021,
      venue: "npj Quantum Information",
      matched: true,
    },
  ]
  return papers
})
</script>

<template>
  <div v-if="expert" class="h-full flex flex-col">
    <!-- Expert header -->
    <div class="px-6 py-5 border-b border-[#e5e7eb]">
      <div class="flex items-start justify-between">
        <div class="flex items-center gap-3 min-w-0">
          <button
            @click="emit('close')"
            class="shrink-0 w-6 h-6 flex items-center justify-center text-[#6b7280] hover:text-[#111827] hover:bg-[#f3f4f6] rounded transition-colors"
            title="Collapse panel"
          >
            <svg class="w-3.5 h-3.5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M15 19l-7-7 7-7" />
            </svg>
          </button>
          <h2 class="text-[18px] font-semibold text-[#111827] m-0 leading-tight truncate">{{ expert.author }}</h2>
          <div class="flex flex-wrap items-center gap-2 mt-2">
            <span class="inline-flex items-center px-2.5 py-0.5 text-[11px] font-medium uppercase tracking-[0.04em] bg-[#f8fafc] text-[#6b7280] border border-[#e5e7eb] rounded">
              {{ expert.institution }}
            </span>
            <span class="inline-flex items-center px-2.5 py-0.5 text-[11px] font-medium uppercase tracking-[0.04em] bg-[#f8fafc] text-[#6b7280] border border-[#e5e7eb] rounded">
              {{ expert.first_year }}–{{ expert.last_year }}
            </span>
          </div>
        </div>
        <div class="flex items-center gap-3 shrink-0 ml-4">
          <a
            v-if="expert.openalex_url"
            :href="expert.openalex_url"
            target="_blank"
            class="text-[13px] text-[#2563eb] hover:underline"
          >
            OpenAlex
          </a>
          <a
            v-if="expert.orcid"
            :href="`https://orcid.org/${expert.orcid}`"
            target="_blank"
            class="text-[13px] text-[#2563eb] hover:underline"
          >
            ORCID
          </a>
        </div>
      </div>
    </div>

    <div class="flex-1 overflow-y-auto px-6 py-5 space-y-6">
      <!-- Metrics -->
      <div>
        <div class="text-[11px] font-semibold uppercase tracking-[0.06em] text-[#6b7280] mb-3">Metrics</div>
        <div class="flex gap-8">
          <div>
            <div class="text-[11px] text-[#6b7280] uppercase tracking-[0.04em] mb-0.5">Works</div>
            <div class="text-[16px] font-semibold text-[#111827]">{{ formatNumber(expert.metrics.works_count) }}</div>
          </div>
          <div>
            <div class="text-[11px] text-[#6b7280] uppercase tracking-[0.04em] mb-0.5">Citations</div>
            <div class="text-[16px] font-semibold text-[#111827]">{{ formatNumber(expert.metrics.citations) }}</div>
          </div>
          <div>
            <div class="text-[11px] text-[#6b7280] uppercase tracking-[0.04em] mb-0.5">h-index</div>
            <div class="text-[16px] font-semibold text-[#111827]">{{ expert.metrics.h_index }}</div>
          </div>
        </div>
      </div>

      <!-- Research Topics (collapsible, default collapsed) -->
      <div>
        <button
          @click="topicsOpen = !topicsOpen"
          class="flex items-center justify-between w-full text-left group"
        >
          <span class="text-[11px] font-semibold uppercase tracking-[0.06em] text-[#6b7280]">Research Topics</span>
          <svg
            :class="['w-3.5 h-3.5 text-[#6b7280] transition-transform', topicsOpen ? 'rotate-180' : '']"
            fill="none"
            stroke="currentColor"
            viewBox="0 0 24 24"
          >
            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M19 9l-7 7-7-7" />
          </svg>
        </button>
        <div v-if="topicsOpen" class="mt-3 space-y-2.5">
          <div
            v-for="topic in expert.all_topics"
            :key="topic.topic_name"
            class="flex items-center gap-3"
          >
            <div class="flex-1 min-w-0">
              <div class="flex items-center justify-between mb-1">
                <span class="text-[13px] text-[#111827] truncate">{{ topic.topic_name }}</span>
                <span class="text-[13px] text-[#6b7280] shrink-0 ml-2">{{ topic.count }}</span>
              </div>
              <div class="flex items-center gap-2">
                <div class="flex-1 h-1.5 bg-[#f3f4f6] rounded-full overflow-hidden">
                  <div
                    class="h-full rounded-full bg-[#2563eb]"
                    :style="{ width: (topic.count / maxTopicCount) * 100 + '%' }"
                  ></div>
                </div>
                <span class="text-[11px] text-[#6b7280] shrink-0">{{ topic.subfield }}</span>
              </div>
            </div>
          </div>
        </div>
      </div>

      <!-- Research Papers (collapsible, default collapsed) -->
      <div>
        <button
          @click="papersOpen = !papersOpen"
          class="flex items-center justify-between w-full text-left group"
        >
          <span class="text-[11px] font-semibold uppercase tracking-[0.06em] text-[#6b7280]">Research Papers</span>
          <svg
            :class="['w-3.5 h-3.5 text-[#6b7280] transition-transform', papersOpen ? 'rotate-180' : '']"
            fill="none"
            stroke="currentColor"
            viewBox="0 0 24 24"
          >
            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M19 9l-7 7-7-7" />
          </svg>
        </button>
        <div v-if="papersOpen" class="mt-3 space-y-2.5">
          <div
            v-for="(paper, i) in mockPapers"
            :key="i"
            class="flex items-start gap-3 py-2"
          >
            <div class="flex-1 min-w-0">
              <div class="text-[13px] text-[#111827] leading-snug">{{ paper.title }}</div>
              <div class="flex items-center gap-2 mt-1">
                <span class="text-[12px] text-[#6b7280]">{{ paper.year }}</span>
                <span class="w-0.5 h-0.5 rounded-full bg-[#d1d5db]"></span>
                <span class="text-[12px] text-[#6b7280] truncate">{{ paper.venue }}</span>
                <span
                  v-if="paper.matched"
                  class="text-[11px] text-[#2563eb] shrink-0"
                >Matched</span>
              </div>
            </div>
          </div>
        </div>
      </div>

      <!-- Expert Evidence (max 3 bullets) -->
      <div>
        <div class="text-[11px] font-semibold uppercase tracking-[0.06em] text-[#6b7280] mb-3">Expert Evidence</div>
        <ul class="space-y-1.5 m-0 p-0 list-none">
          <li
            v-for="reason in expert.why.slice(0, 3)"
            :key="reason"
            class="flex items-start gap-2 text-[13px] text-[#111827]"
          >
            <span class="text-[#2563eb] shrink-0 mt-0.5">✓</span>
            <span>{{ reason }}</span>
          </li>
        </ul>
      </div>

      <!-- Contact (always visible) -->
      <div v-if="expert.contacts.length > 0">
        <div class="text-[11px] font-semibold uppercase tracking-[0.06em] text-[#6b7280] mb-3">Contact</div>
        <div class="space-y-2">
          <div
            v-for="contact in expert.contacts"
            :key="contact.label"
            class="flex items-center gap-2.5 text-[13px]"
          >
            <!-- Email icon -->
            <svg
              v-if="contact.type === 'email'"
              class="w-3.5 h-3.5 text-[#6b7280] shrink-0"
              fill="none"
              stroke="currentColor"
              viewBox="0 0 24 24"
            >
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M3 8l7.89 5.26a2 2 0 002.22 0L21 8M5 19h14a2 2 0 002-2V7a2 2 0 00-2-2H5a2 2 0 00-2 2v10a2 2 0 002 2z" />
            </svg>
            <!-- Link icon -->
            <svg
              v-else
              class="w-3.5 h-3.5 text-[#6b7280] shrink-0"
              fill="none"
              stroke="currentColor"
              viewBox="0 0 24 24"
            >
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M13.828 10.172a4 4 0 00-5.656 0l-4 4a4 4 0 105.656 5.656l1.102-1.101m-.758-4.899a4 4 0 005.656 0l4-4a4 4 0 00-5.656-5.656l-1.1 1.1" />
            </svg>
            <span class="text-[#6b7280] min-w-[44px]">{{ contact.label }}</span>
            <a
              v-if="contact.type === 'email'"
              :href="'mailto:' + contact.value"
              class="text-[#2563eb] hover:underline truncate"
            >{{ contact.value }}</a>
            <a
              v-else
              :href="contact.value"
              target="_blank"
              class="text-[#2563eb] hover:underline truncate"
            >{{ contact.value }}</a>
          </div>
        </div>
      </div>
    </div>
  </div>

  <!-- Empty state when no expert selected -->
  <div
    v-else
    class="h-full flex items-center justify-center px-6"
  >
    <div class="text-center">
      <p class="text-[14px] text-[#6b7280]">Select an expert to view details</p>
    </div>
  </div>
</template>
