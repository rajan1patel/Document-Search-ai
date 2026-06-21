<script setup lang="ts">
import { ref } from "vue"
import { api } from "~/utils/api"

const file = ref<File | null>(null)
const uploading = ref(false)
const error = ref<string | null>(null)
const success = ref(false)
const fileInput = ref<HTMLInputElement | null>(null)

const emit = defineEmits(["uploaded"])

function chooseFile(e: any) {
  file.value = e.target.files[0]
  error.value = null
}

async function upload() {
  if (!file.value) {
    error.value = "Please select a file"
    return
  }

  uploading.value = true
  error.value = null

  try {
    const form = new FormData()
    form.append("file", file.value)

    await api.post("/documents/upload", form, {
      headers: {
        "Content-Type": "multipart/form-data",
      },
    })

    success.value = true
    file.value = null
    setTimeout(() => {
      emit("uploaded")
    }, 1000)
  } catch (err: any) {
    error.value = err.message || "Upload failed"
  } finally {
    uploading.value = false
  }
}
</script>

<template>
<div class="space-y-6">
  <div v-if="success" class="bg-green-50 border border-green-200 rounded-lg p-4">
    <p class="text-green-800 font-medium">✅ Document uploaded successfully!</p>
  </div>

  <div v-if="error" class="bg-red-50 border border-red-200 rounded-lg p-4">
    <p class="text-red-800 font-medium">❌ {{ error }}</p>
  </div>

  <div
    class="border-2 border-dashed border-blue-300 rounded-lg p-8 text-center hover:bg-blue-50 transition duration-200 cursor-pointer"
    @click="fileInput?.click()"
  >
    <input
      ref="fileInput"
      type="file"
      class="hidden"
      @change="chooseFile"
    />
    <div class="text-4xl mb-3">📄</div>
    <h3 class="text-lg font-semibold text-gray-900 mb-2">
      {{ file?.name || "Click to upload or drag and drop" }}
    </h3>
    <p class="text-gray-600 text-sm mb-4">
      {{ file ? `File selected: ${(file.size / 1024 / 1024).toFixed(2)} MB` : "Supported formats: PDF, DOCX, TXT, and more" }}
    </p>
    <button
      type="button"
      class="inline-block bg-blue-600 hover:bg-blue-700 text-white font-semibold py-2 px-6 rounded-lg transition duration-200"
    >
      Choose File
    </button>
  </div>

  <button
    @click="upload"
    :disabled="!file || uploading"
    class="w-full py-3 px-6 bg-blue-600 hover:bg-blue-700 disabled:bg-gray-400 text-white font-semibold rounded-lg transition duration-200 disabled:cursor-not-allowed"
  >
    {{ uploading ? "Uploading..." : "Upload Document" }}
  </button>
</div>
</template>