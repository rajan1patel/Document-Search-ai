<script setup lang="ts">
import { ref, nextTick, watch } from "vue"
import { useChat, type Message, type Source, type GroupedSource } from "~/composables/useChat"

const { sendMessage } = useChat()

const query = ref("")
const messages = ref<Message[]>([])
const loading = ref(false)
const error = ref<string | null>(null)
const chatContainer = ref<HTMLElement | null>(null)
const textareaRef = ref<HTMLTextAreaElement | null>(null)

function autoResize() {
  const el = textareaRef.value
  if (!el) return
  el.style.height = "auto"
  el.style.height = el.scrollHeight + "px"
}

// Auto-scroll to bottom when new messages arrive
async function scrollToBottom() {
  await nextTick()
  if (chatContainer.value) {
    chatContainer.value.scrollTop = chatContainer.value.scrollHeight
  }
}

watch(messages, scrollToBottom, { deep: true })

async function submit() {
  const text = query.value.trim()
  if (!text) return

  // Add user message
  messages.value.push({ role: "user", content: text })
  query.value = ""
  loading.value = true
  error.value = null

  try {
    const history = messages.value.slice(0, -1) // exclude the just-added user msg
    const { answer, sources, groupedSources } = await sendMessage(text, history)

    messages.value.push({ role: "assistant", content: answer, sources, groupedSources })
  } catch (err: any) {
    error.value = err?.response?.data?.detail || err.message || "Failed to get response"
    // Remove the user message on error so they can retry
    messages.value.pop()
  } finally {
    loading.value = false
  }
}

function getSourceIcon(filename: string | null): string {
  if (!filename) return "📄"
  const ext = filename.split(".").pop()?.toLowerCase()
  if (ext === "pdf") return "📕"
  if (ext === "docx" || ext === "doc") return "📘"
  if (ext === "txt") return "📄"
  return "📄"
}

function totalSourceCount(groups: GroupedSource[]): number {
  return groups.reduce((sum, g) => sum + g.total_chunks, 0)
}
</script>

<template>
  <div class="flex flex-col h-full">
    <!-- ── Messages area ── -->
    <div
      ref="chatContainer"
      class="flex-1 overflow-y-auto px-4 py-6 space-y-4 scroll-smooth"
    >
      <!-- Empty state -->
      <div
        v-if="messages.length === 0 && !loading"
        class="flex flex-col items-center justify-center h-full text-center py-16"
      >
        <div class="text-7xl mb-6 opacity-80">💬</div>
        <h3 class="text-2xl font-semibold text-gray-800 mb-2">
          Chat with your documents
        </h3>
        <p class="text-gray-500 max-w-md">
          Ask questions about your uploaded documents and get AI-powered answers
          with source citations.
        </p>
        <div class="mt-8 grid grid-cols-1 sm:grid-cols-2 gap-3 text-left">
          <div
            class="px-4 py-3 bg-gray-50 rounded-xl border border-gray-200 text-sm text-gray-600 cursor-pointer hover:bg-blue-50 hover:border-blue-200 transition"
            @click="query = 'What documents do I have?'; submit()"
          >
            <span class="text-lg mr-2">📋</span>
            "What documents do I have?"
          </div>
          <div
            class="px-4 py-3 bg-gray-50 rounded-xl border border-gray-200 text-sm text-gray-600 cursor-pointer hover:bg-blue-50 hover:border-blue-200 transition"
            @click="query = 'Summarize the key topics in my documents'; submit()"
          >
            <span class="text-lg mr-2">📝</span>
            "Summarize my documents"
          </div>
          <div
            class="px-4 py-3 bg-gray-50 rounded-xl border border-gray-200 text-sm text-gray-600 cursor-pointer hover:bg-blue-50 hover:border-blue-200 transition"
            @click="query = 'Find information about machine learning'; submit()"
          >
            <span class="text-lg mr-2">🤖</span>
            "Find info about ML"
          </div>
          <div
            class="px-4 py-3 bg-gray-50 rounded-xl border border-gray-200 text-sm text-gray-600 cursor-pointer hover:bg-blue-50 hover:border-blue-200 transition"
            @click="query = 'What are the main conclusions in my documents?'; submit()"
          >
            <span class="text-lg mr-2">🎯</span>
            "What are the conclusions?"
          </div>
        </div>
      </div>

      <!-- Messages -->
      <template v-for="(msg, idx) in messages" :key="idx">
        <!-- User message -->
        <div v-if="msg.role === 'user'" class="flex justify-end">
          <div
            class="max-w-[80%] bg-gradient-to-r from-blue-600 to-blue-500 text-white rounded-2xl rounded-br-sm px-5 py-3 shadow-md"
          >
            <p class="text-sm leading-relaxed whitespace-pre-wrap">{{ msg.content }}</p>
          </div>
        </div>

        <!-- Assistant message -->
        <div v-else class="flex justify-start">
          <div class="max-w-[85%]">
            <div
              class="bg-white border border-gray-200 text-gray-800 rounded-2xl rounded-bl-sm px-5 py-3 shadow-sm"
            >
              <div class="flex items-start gap-2 mb-2">
                <span class="text-lg flex-shrink-0">🤖</span>
                <span class="text-xs font-semibold text-blue-600 mt-1">DocSearch AI</span>
              </div>
              <p class="text-sm leading-relaxed whitespace-pre-wrap">{{ msg.content }}</p>
            </div>

            <!-- Sources (grouped by file) -->
            <div v-if="msg.groupedSources && msg.groupedSources.length > 0" class="mt-2 ml-2">
              <details class="group">
                <summary
                  class="flex items-center gap-1.5 text-xs text-gray-500 hover:text-blue-600 cursor-pointer font-medium transition-colors select-none"
                >
                  <svg
                    class="w-3.5 h-3.5 transition-transform group-open:rotate-90"
                    fill="none"
                    stroke="currentColor"
                    viewBox="0 0 24 24"
                  >
                    <path
                      stroke-linecap="round"
                      stroke-linejoin="round"
                      stroke-width="2"
                      d="M9 5l7 7-7 7"
                    />
                  </svg>
                  {{ totalSourceCount(msg.groupedSources) }} source{{ totalSourceCount(msg.groupedSources) > 1 ? "s" : "" }}
                  from {{ msg.groupedSources.length }} file{{ msg.groupedSources.length > 1 ? "s" : "" }}
                </summary>
                <div class="mt-2 space-y-2">
                  <div
                    v-for="(group, gi) in msg.groupedSources"
                    :key="gi"
                    class="bg-gray-50 rounded-lg border border-gray-100 overflow-hidden"
                  >
                    <!-- File header -->
                    <div class="flex items-center gap-2 px-3 py-2 bg-gray-100/70 border-b border-gray-100">
                      <span class="text-sm flex-shrink-0">{{ getSourceIcon(group.filename) }}</span>
                      <span class="text-xs font-semibold text-gray-700 truncate">{{ group.filename }}</span>
                      <span class="text-[10px] text-gray-400 ml-auto">
                        {{ group.total_chunks }} excerpt{{ group.total_chunks > 1 ? "s" : "" }}
                        · {{ (group.avg_score * 100).toFixed(0) }}% match
                      </span>
                    </div>
                    <!-- Chunks -->
                    <div class="space-y-1 p-2">
                      <div
                        v-for="(chunk, ci) in group.chunks"
                        :key="ci"
                        class="text-xs text-gray-500 pl-2 border-l-2 border-blue-200"
                      >
                        <span v-if="chunk.page" class="text-[10px] text-blue-500 font-medium">p.{{ chunk.page }}</span>
                        <p class="mt-0.5 line-clamp-2">{{ chunk.chunk }}</p>
                      </div>
                    </div>
                  </div>
                </div>
              </details>
            </div>
          </div>
        </div>
      </template>

      <!-- Typing indicator -->
      <div v-if="loading" class="flex justify-start">
        <div
          class="bg-white border border-gray-200 rounded-2xl rounded-bl-sm px-5 py-4 shadow-sm"
        >
          <div class="flex items-center gap-1">
            <span class="text-lg mr-1">🤖</span>
            <span class="typing-dot w-2 h-2 bg-blue-500 rounded-full animate-bounce" style="animation-delay: 0ms"></span>
            <span class="typing-dot w-2 h-2 bg-blue-500 rounded-full animate-bounce" style="animation-delay: 150ms"></span>
            <span class="typing-dot w-2 h-2 bg-blue-500 rounded-full animate-bounce" style="animation-delay: 300ms"></span>
          </div>
        </div>
      </div>
    </div>

    <!-- Error banner -->
    <div
      v-if="error"
      class="mx-4 mb-2 bg-red-50 border border-red-200 rounded-xl px-4 py-3 flex items-center justify-between"
    >
      <div class="flex items-center gap-2">
        <span class="text-red-500 text-lg">⚠️</span>
        <p class="text-sm text-red-700">{{ error }}</p>
      </div>
      <button
        @click="error = null"
        class="text-red-400 hover:text-red-600 text-lg leading-none"
      >
        &times;
      </button>
    </div>

    <!-- ── Input area ── -->
    <div class="border-t border-gray-200 bg-white px-4 py-4">
      <form @submit.prevent="submit" class="flex items-end gap-3 max-w-4xl mx-auto">
        <div class="flex-1 relative">
          <textarea
            ref="textareaRef"
            v-model="query"
            placeholder="Ask a question about your documents..."
            rows="1"
            class="w-full px-4 py-3 pr-12 border border-gray-300 rounded-xl focus:ring-2 focus:ring-blue-500 focus:border-transparent outline-none resize-none transition text-sm bg-gray-50 hover:bg-white focus:bg-white"
            @keydown.enter.exact="submit"
            @input="autoResize"
          ></textarea>
        </div>
        <button
          type="submit"
          :disabled="loading || !query.trim()"
          class="flex-shrink-0 bg-gradient-to-r from-blue-600 to-blue-500 hover:from-blue-700 hover:to-blue-600 disabled:from-gray-300 disabled:to-gray-300 text-white font-semibold p-3.5 rounded-xl transition duration-200 disabled:cursor-not-allowed shadow-md hover:shadow-lg"
        >
          <svg
            v-if="!loading"
            class="w-5 h-5"
            fill="none"
            stroke="currentColor"
            viewBox="0 0 24 24"
          >
            <path
              stroke-linecap="round"
              stroke-linejoin="round"
              stroke-width="2"
              d="M12 19V5m0 0l-7 7m7-7l7 7"
            />
          </svg>
          <svg
            v-else
            class="w-5 h-5 animate-spin"
            fill="none"
            viewBox="0 0 24 24"
          >
            <circle
              class="opacity-25"
              cx="12"
              cy="12"
              r="10"
              stroke="currentColor"
              stroke-width="4"
            ></circle>
            <path
              class="opacity-75"
              fill="currentColor"
              d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4z"
            ></path>
          </svg>
        </button>
      </form>
      <p class="text-xs text-gray-400 text-center mt-2">
        Responses are AI-generated. Verify important information from your sources.
      </p>
    </div>
  </div>
</template>

<style scoped>
/* Custom scrollbar */
.chat-scrollbar::-webkit-scrollbar {
  width: 6px;
}
.chat-scrollbar::-webkit-scrollbar-track {
  background: transparent;
}
.chat-scrollbar::-webkit-scrollbar-thumb {
  background: #d1d5db;
  border-radius: 3px;
}
.chat-scrollbar::-webkit-scrollbar-thumb:hover {
  background: #9ca3af;
}

/* Typing dots animation */
.typing-dot {
  animation: bounce 1.4s infinite ease-in-out both;
}

@keyframes bounce {
  0%, 80%, 100% {
    transform: scale(0);
    opacity: 0.5;
  }
  40% {
    transform: scale(1);
    opacity: 1;
  }
}

/* Smooth scroll for the chat container */
#chatContainer {
  scroll-behavior: smooth;
}
</style>
