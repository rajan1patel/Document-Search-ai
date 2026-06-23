<script setup lang="ts">
import { useAuthStore } from "~/stores/auth"

const auth = useAuthStore()
const router = useRouter()

function handleLogout() {
  auth.logout()
  router.push("/login")
}
</script>

<template>
<nav class="bg-white shadow-md border-b border-gray-200">
  <div class="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
    <div class="flex justify-between items-center h-16">
      <NuxtLink to="/" class="flex items-center gap-2 hover:opacity-80 transition">
        <span class="text-2xl font-bold text-blue-600">📄</span>
        <span class="text-xl font-bold text-gray-900">DocSearch</span>
      </NuxtLink>
      
      <!-- Authenticated nav links -->
      <div v-if="auth.token" class="flex gap-1 items-center">
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

        <NuxtLink
          to="/chat"
          class="px-4 py-2 text-gray-700 hover:text-blue-600 font-medium transition duration-200 border-b-2 border-transparent hover:border-blue-600"
        >
          💬 Chat
        </NuxtLink>

        <button
          @click="handleLogout"
          class="ml-4 px-4 py-2 text-sm text-red-600 hover:text-red-700 hover:bg-red-50 font-medium transition duration-200 rounded-lg border border-red-200 hover:border-red-300"
        >
          🚪 Logout
        </button>
      </div>

      <!-- Unauthenticated nav links -->
      <div v-else class="flex gap-2 items-center">
        <NuxtLink
          to="/login"
          class="px-4 py-2 text-gray-700 hover:text-blue-600 font-medium transition duration-200"
        >
          Sign In
        </NuxtLink>

        <NuxtLink
          to="/register"
          class="px-4 py-2 bg-blue-600 hover:bg-blue-700 text-white font-semibold rounded-lg transition duration-200"
        >
          Register
        </NuxtLink>
      </div>
    </div>
  </div>
</nav>
</template>