export default defineNuxtRouteMiddleware((to, from) => {
  if (import.meta.server) {
    return
  }

  const token = localStorage.getItem("token")

  if (token) {
    return navigateTo("/dashboard")
  }
})
