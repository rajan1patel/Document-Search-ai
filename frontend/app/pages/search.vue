<template>
<div class="min-h-screen bg-gradient-to-br from-slate-50 to-slate-100">
  <Navbar />
  
  <div class="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-12">
    <div class="mb-8">
      <h1 class="text-4xl font-bold text-gray-900 mb-2">AI Document Search</h1>
      <p class="text-gray-600">Search your documents using AI-powered semantic search</p>
    </div>

    <div class="bg-white rounded-lg shadow-md border border-gray-200 p-8">
      <SearchBox />
    </div>
  </div>
</div>
</template>