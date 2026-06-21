<script setup lang="ts">
const router = useRouter()
</script>

<template>
<div class="min-h-screen bg-gradient-to-br from-blue-50 via-white to-purple-50">
  <Navbar />
  
  <div class="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-20">
    <div class="text-center mb-16">
      <h1 class="text-5xl sm:text-6xl font-bold text-gray-900 mb-6">
        Smart Document <span class="text-blue-600">Search</span>
      </h1>
      <p class="text-xl text-gray-600 mb-8 max-w-2xl mx-auto">
        Upload, search, and organize your documents with AI-powered semantic search capabilities
      </p>
      
      <div class="flex flex-col sm:flex-row gap-4 justify-center">
        <NuxtLink
          to="/upload"
          class="inline-flex items-center justify-center gap-2 bg-blue-600 hover:bg-blue-700 text-white font-semibold py-4 px-8 rounded-lg transition duration-200 shadow-lg hover:shadow-xl text-lg"
        >
          <span>📤</span>
          Upload Document
        </NuxtLink>
        <NuxtLink
          to="/documents"
          class="inline-flex items-center justify-center gap-2 bg-white hover:bg-gray-50 text-blue-600 font-semibold py-4 px-8 rounded-lg transition duration-200 shadow-md hover:shadow-lg text-lg border-2 border-blue-600"
        >
          <span>📁</span>
          View Documents
        </NuxtLink>
      </div>
    </div>

    <div class="grid md:grid-cols-3 gap-8 mt-16">
      <div class="bg-white rounded-xl shadow-md p-8 border border-gray-200 hover:shadow-lg transition duration-200">
        <div class="text-4xl mb-4">🚀</div>
        <h3 class="text-xl font-semibold text-gray-900 mb-2">Fast Upload</h3>
        <p class="text-gray-600">Quickly upload your documents in multiple formats</p>
      </div>
      
      <div class="bg-white rounded-xl shadow-md p-8 border border-gray-200 hover:shadow-lg transition duration-200">
        <div class="text-4xl mb-4">🔍</div>
        <h3 class="text-xl font-semibold text-gray-900 mb-2">Smart Search</h3>
        <p class="text-gray-600">Find documents using AI-powered semantic search</p>
      </div>
      
      <div class="bg-white rounded-xl shadow-md p-8 border border-gray-200 hover:shadow-lg transition duration-200">
        <div class="text-4xl mb-4">💾</div>
        <h3 class="text-xl font-semibold text-gray-900 mb-2">Organize</h3>
        <p class="text-gray-600">Manage and organize all your documents efficiently</p>
      </div>
    </div>
  </div>
</div>
</template>
