<script setup lang="ts">
definePageMeta({
  middleware: "auth",
})

import { ref } from "vue"

import { api } from "~/utils/api"

interface Document {
  id: number
  filename: string
  file_type: string
  file_size: number
  status: string
}

const documents = ref<Document[]>([])

const loading = ref(false)



async function loadDocuments(){

    loading.value = true

    try {

    const res = await api.get(
        "/documents"
    )

    documents.value = res.data

    } finally {

    loading.value = false

    }

}



async function deleteDocument(id:number){

    await api.delete(
        `/documents/${id}`
    )


    await loadDocuments()

}



loadDocuments()


</script>



<template>

<div class="min-h-screen bg-gradient-to-br from-slate-50 to-slate-100">
  <Navbar />
  
  <div class="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-12">
    <div class="mb-8">
      <h1 class="text-4xl font-bold text-gray-900 mb-2">My Documents</h1>
      <p class="text-gray-600">Manage and organize your uploaded documents</p>
    </div>

    <div class="mb-6">
      <NuxtLink
        to="/upload"
        class="inline-flex items-center gap-2 bg-blue-600 hover:bg-blue-700 text-white font-semibold py-3 px-6 rounded-lg transition duration-200 shadow-md hover:shadow-lg"
      >
        <span>📤</span>
        Upload Document
      </NuxtLink>
    </div>

    <div v-if="loading" class="text-center py-12">
      <p class="text-gray-600 text-lg">Loading documents...</p>
    </div>

    <div v-else-if="documents.length === 0" class="text-center py-12">
      <p class="text-gray-500 text-lg mb-4">No documents yet</p>
      <NuxtLink
        to="/upload"
        class="text-blue-600 hover:text-blue-700 underline"
      >
        Upload your first document
      </NuxtLink>
    </div>

    <div v-else class="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
      <div
        v-for="doc in documents"
        :key="doc.id"
        class="bg-white rounded-lg shadow-md hover:shadow-lg transition duration-200 border border-gray-200 overflow-hidden"
      >
        <div class="p-6">
          <div class="flex items-start justify-between mb-4">
            <div class="flex-1">
              <h3 class="text-lg font-semibold text-gray-900 truncate">
                {{ doc.filename }}
              </h3>
              <p class="text-sm text-gray-500 mt-1">{{ doc.file_type }}</p>
            </div>
            <span
              :class="{
                'bg-green-100 text-green-800': doc.status === 'completed',
                'bg-yellow-100 text-yellow-800': doc.status === 'processing',
                'bg-red-100 text-red-800': doc.status === 'failed',
                'bg-blue-100 text-blue-800': doc.status === 'pending',
              }"
              class="px-3 py-1 rounded-full text-xs font-medium whitespace-nowrap"
            >
              {{ doc.status }}
            </span>
          </div>
          
          <div class="mb-4">
            <p class="text-sm text-gray-600">
              <span class="font-medium">Size:</span>
              {{ (doc.file_size / 1024 / 1024).toFixed(2) }} MB
            </p>
          </div>
          
          <button
            @click="deleteDocument(doc.id)"
            class="w-full bg-red-50 hover:bg-red-100 text-red-600 font-medium py-2 px-4 rounded-lg transition duration-200 border border-red-200"
          >
            🗑️ Delete
          </button>
        </div>
      </div>
    </div>
  </div>
</div>

</template>
