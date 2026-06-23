import { defineStore } from "pinia"
import { api } from "../utils/api"

interface AuthUser {
  id: number
  email: string
}

export const useAuthStore = defineStore("auth", {
  state: () => ({
    user: null as AuthUser | null,
    token: null as string | null,
  }),

  getters: {
    isAuthenticated: (state) => !!state.token,
  },

  actions: {
    initialize() {
      if (!process.client) {
        return
      }

      const token = localStorage.getItem("token")
      if (token) {
        this.token = token
      }
    },

    async login(email: string, password: string) {
      const res = await api.post("/auth/login", {
        email,
        password,
      })

      const token = res.data.access_token as string
      this.token = token
      this.user = res.data.user ?? null
      localStorage.setItem("token", token)
    },

    logout() {
      localStorage.removeItem("token")
      this.token = null
      this.user = null
    },
  },
})
