<script setup lang="ts">
import { ref } from "vue"
import { useRouter } from "vue-router"
import { useAuthStore } from "~/stores/auth"

const email = ref("")
const password = ref("")
const loading = ref(false)
const error = ref<string | null>(null)

const auth = useAuthStore()
const router = useRouter()

async function submit() {
  if (!email.value || !password.value) {
    error.value = "Please fill in all fields"
    return
  }

  loading.value = true
  error.value = null

  try {
    await auth.login(email.value, password.value)
    router.push("/dashboard")
  } catch (err: any) {
    error.value = err.message || "Login failed"
  } finally {
    loading.value = false
  }
}
</script>

<template>
<div class="min-h-screen bg-gradient-to-br from-blue-600 to-blue-800 flex items-center justify-center px-4">
  <div class="w-full max-w-md">
    <div class="bg-white rounded-lg shadow-lg p-8">
      <div class="text-center mb-8">
        <div class="text-5xl mb-3">📄</div>
        <h1 class="text-3xl font-bold text-gray-900">DocSearch</h1>
        <p class="text-gray-600 mt-2">Sign in to your account</p>
      </div>

      <div v-if="error" class="mb-6 bg-red-50 border border-red-200 rounded-lg p-4">
        <p class="text-red-800 font-medium">{{ error }}</p>
      </div>

      <form @submit.prevent="submit" class="space-y-4">
        <div>
          <label for="email" class="block text-sm font-medium text-gray-700 mb-2"
            >Email Address</label
          >
          <input
            id="email"
            v-model="email"
            type="email"
            placeholder="you@example.com"
            class="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-600 focus:border-transparent outline-none transition"
          />
        </div>

        <div>
          <label for="password" class="block text-sm font-medium text-gray-700 mb-2"
            >Password</label
          >
          <input
            id="password"
            v-model="password"
            type="password"
            placeholder="••••••••"
            class="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-600 focus:border-transparent outline-none transition"
          />
        </div>

        <button
          type="submit"
          :disabled="loading"
          class="w-full bg-blue-600 hover:bg-blue-700 disabled:bg-gray-400 text-white font-semibold py-2 px-4 rounded-lg transition duration-200 disabled:cursor-not-allowed"
        >
          {{ loading ? "Signing in..." : "Sign In" }}
        </button>
      </form>

      <p class="text-center text-gray-600 mt-6">
        Don't have an account?
        <NuxtLink to="/register" class="text-blue-600 hover:text-blue-700 font-medium"
          >Register here</NuxtLink
        >
      </p>
    </div>
  </div>
</div>
</template>