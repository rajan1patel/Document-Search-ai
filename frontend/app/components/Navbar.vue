<template>
<nav class="bg-white shadow-md border-b border-gray-200">
  <div class="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
    <div class="flex justify-between items-center h-16">
      <div class="flex items-center gap-2">
        <span class="text-2xl font-bold text-blue-600">📄</span>
        <span class="text-xl font-bold text-gray-900">DocSearch</span>
      </div>
      
      <div class="flex gap-1">
        <NuxtLink
          to="/dashboard"
          class="px-4 py-2 text-gray-700 hover:text-blue-600 font-medium transition duration-200 border-b-2 border-transparent hover:border-blue-600"
        >
          📊 Dashboard
        </NuxtLink>
        
        <NuxtLink
          to="/documents"
          class="px-4 py-2 text-gray-700 hover:text-blue-600 font-medium transition duration-200 border-b-2 border-transparent hover:border-blue-600"
        >
          📁 Documents
        </NuxtLink>
        
        <NuxtLink
          to="/search"
          class="px-4 py-2 text-gray-700 hover:text-blue-600 font-medium transition duration-200 border-b-2 border-transparent hover:border-blue-600"
        >
          🔍 Search
        </NuxtLink>
      </div>
    </div>
  </div>
</nav>
</template>