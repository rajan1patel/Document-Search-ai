<script setup lang="ts">
import { ref, onMounted } from "vue"
import { api } from "~/utils/api"

const data = ref({
  total_documents: 0,
  processed_documents: 0,
})

onMounted(async () => {
  const res = await api.get("/dashboard")
  data.value = {
    total_documents: res.data.total_documents || 0,
    processed_documents: res.data.processed_documents || res.data.total_documents || 0,
  }
})
</script>

<template>
<div class="min-h-screen bg-gradient-to-br from-slate-50 to-slate-100">
  <Navbar />
  
  <div class="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-12">
    <div class="mb-8">
      <h1 class="text-4xl font-bold text-gray-900 mb-2">Dashboard</h1>
      <p class="text-gray-600">Welcome back! Here's your document overview</p>
    </div>

    <div class="grid grid-cols-1 md:grid-cols-2 gap-6 mb-8">
      <div class="bg-white rounded-lg shadow-md border border-gray-200 p-8 hover:shadow-lg transition duration-200">
        <div class="flex items-center justify-between">
          <div>
            <p class="text-gray-600 text-sm font-medium">Total Documents</p>
            <p class="text-4xl font-bold text-gray-900 mt-2">{{ data?.total_documents || 0 }}</p>
          </div>
          <div class="text-5xl text-blue-600">📁</div>
        </div>
      </div>

      <div class="bg-white rounded-lg shadow-md border border-gray-200 p-8 hover:shadow-lg transition duration-200">
        <div class="flex items-center justify-between">
          <div>
            <p class="text-gray-600 text-sm font-medium">Documents Processed</p>
            <p class="text-4xl font-bold text-gray-900 mt-2">{{ data?.processed_documents || 0 }}</p>
          </div>
          <div class="text-5xl text-green-600">✅</div>
        </div>
      </div>
    </div>

    <div class="bg-white rounded-lg shadow-md border border-gray-200 p-8">
      <h2 class="text-2xl font-bold text-gray-900 mb-6">Quick Actions</h2>
      <div class="grid grid-cols-1 md:grid-cols-2 gap-4">
        <NuxtLink
          to="/upload"
          class="flex items-center gap-3 p-4 border-2 border-blue-200 rounded-lg hover:bg-blue-50 transition duration-200"
        >
          <span class="text-3xl">📤</span>
          <div>
            <h3 class="font-semibold text-gray-900">Upload Document</h3>
            <p class="text-sm text-gray-600">Add a new document</p>
          </div>
        </NuxtLink>

        <NuxtLink
          to="/documents"
          class="flex items-center gap-3 p-4 border-2 border-green-200 rounded-lg hover:bg-green-50 transition duration-200"
        >
          <span class="text-3xl">📁</span>
          <div>
            <h3 class="font-semibold text-gray-900">View Documents</h3>
            <p class="text-sm text-gray-600">Manage your files</p>
          </div>
        </NuxtLink>

        <NuxtLink
          to="/search"
          class="flex items-center gap-3 p-4 border-2 border-purple-200 rounded-lg hover:bg-purple-50 transition duration-200"
        >
          <span class="text-3xl">🔍</span>
          <div>
            <h3 class="font-semibold text-gray-900">Search</h3>
            <p class="text-sm text-gray-600">Find your documents</p>
          </div>
        </NuxtLink>

        <NuxtLink
          to="/chat"
          class="flex items-center gap-3 p-4 border-2 border-amber-200 rounded-lg hover:bg-amber-50 transition duration-200"
        >
          <span class="text-3xl">💬</span>
          <div>
            <h3 class="font-semibold text-gray-900">AI Chat</h3>
            <p class="text-sm text-gray-600">Chat with your documents</p>
          </div>
        </NuxtLink>
      </div>
    </div>
  </div>
</div>
</template>
