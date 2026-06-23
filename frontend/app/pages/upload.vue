<script setup>
definePageMeta({
  middleware: "auth",
})

const router = useRouter()
</script>

<template>
<div class="min-h-screen bg-gradient-to-br from-slate-50 to-slate-100">
  <Navbar />
  
  <div class="max-w-4xl mx-auto px-4 sm:px-6 lg:px-8 py-12">
    <div class="mb-8">
      <h1 class="text-4xl font-bold text-gray-900 mb-2">Upload Document</h1>
      <p class="text-gray-600">Upload your documents to start searching and organizing them</p>
    </div>

    <div class="bg-white rounded-lg shadow-md border border-gray-200 p-8">
      <DocumentUpload
        @uploaded="router.push('/documents')"
      />
    </div>
  </div>
</div>
</template>