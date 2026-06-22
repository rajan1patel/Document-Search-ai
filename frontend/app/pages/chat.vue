<script setup lang="ts">
definePageMeta({
  middleware: "auth",
})
</script>

<template>
  <div class="h-screen flex flex-col bg-gradient-to-br from-slate-50 via-white to-blue-50">
    <Navbar />

    <!-- Header -->
    <div class="border-b border-gray-200 bg-white/80 backdrop-blur-sm">
      <div class="max-w-5xl mx-auto px-4 sm:px-6 py-4 flex items-center justify-between">
        <div>
          <h1 class="text-xl font-bold text-gray-900 flex items-center gap-2">
            <span>💬</span>
            AI Chat Assistant
          </h1>
          <p class="text-sm text-gray-500">Ask questions about your documents</p>
        </div>
      </div>
    </div>

    <!-- Chat area -->
    <div class="flex-1 max-w-5xl w-full mx-auto flex flex-col overflow-hidden">
      <ChatBox />
    </div>
  </div>
</template>
