<script setup lang="ts">
import type { ResearchExpertOutput } from "~/composables/useResearchExpert"

defineProps<{
  experts: ResearchExpertOutput[]
  selectedIndex: number | null
}>()

defineEmits<{
  select: [index: number]
}>()
</script>

<template>
  <div>
    <div class="px-5 py-3 border-b border-[#e5e7eb]">
      <span class="text-[11px] font-semibold uppercase tracking-[0.06em] text-[#6b7280]">Ranked Experts</span>
    </div>
    <div class="divide-y divide-[#e5e7eb]">
      <button
        v-for="(expert, index) in experts"
        :key="expert.author_id"
        @click="$emit('select', index)"
        :class="[
          'w-full flex items-center gap-3 px-5 py-3 text-left transition-colors cursor-pointer',
          selectedIndex === index
            ? 'bg-[#eff6ff] border-l-[3px] border-[#2563eb] pl-[17px]'
            : 'bg-white hover:bg-[#f8fafc] border-l-[3px] border-transparent pl-[17px]'
        ]"
      >
        <span
          :class="[
            'text-sm font-medium min-w-[20px]',
            selectedIndex === index ? 'text-[#2563eb]' : 'text-[#6b7280]'
          ]"
        >
          {{ index + 1 }}
        </span>
        <div class="flex-1 min-w-0">
          <div
            :class="[
              'text-sm font-medium truncate',
              selectedIndex === index ? 'text-[#111827]' : 'text-[#111827]'
            ]"
          >
            {{ expert.author }}
          </div>
          <div class="text-[13px] text-[#6b7280] truncate mt-0.5">
            {{ expert.institution }}
          </div>
        </div>
      </button>
    </div>
  </div>
</template>
