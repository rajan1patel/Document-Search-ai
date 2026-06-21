export default defineNuxtRouteMiddleware((to) => {
  const token =
    typeof window !== "undefined" ? localStorage.getItem("token") : null

  if (!token && to.path !== "/login" && to.path !== "/register") {
    return navigateTo("/login")
  }
})