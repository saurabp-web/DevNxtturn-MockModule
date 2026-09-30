<template>
  <div class="admin-shell">
    <!-- Defence-in-depth: the router guard already redirects unauthenticated/
         non-staff visitors to Django's /admin/login/. This runtime check
         guards against the layout briefly rendering before that async
         session check resolves. -->
    <template v-if="isChecking">
      <div class="admin-loading">Checking admin session…</div>
    </template>
    <template v-else-if="adminUser?.is_staff">
      <AdminSidebar :collapsed="sidebarCollapsed" @navigate="handleNavigate" />
      <div class="admin-main">
        <AdminTopbar @toggleSidebar="sidebarCollapsed = !sidebarCollapsed" />
        <div class="admin-content">
          <!-- CHANGED: was <slot />, which only fills when a parent
               explicitly wraps content around <AdminLayout>. But
               router/index.ts registers AdminLayout as a parent ROUTE
               with nested children (DashboardView, etc.) — Vue Router
               injects matched child routes into <router-view />, not
               into a slot. This was why the sidebar/topbar always
               rendered (they're part of AdminLayout itself) but the
               page content was always blank, regardless of what
               DashboardView.vue contained. -->
          <router-view />
        </div>
      </div>
    </template>
    <div v-else class="access-denied">
      <h2>Access Denied</h2>
      <p>You don't have admin access. Contact your site owner if you think this is a mistake.</p>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { fetchAdminSessionUser, type AdminSessionUser } from '@/services/adminAuth'
import AdminSidebar from './AdminSidebar.vue'
import AdminTopbar from './AdminTopbar.vue'

const router = useRouter()
const sidebarCollapsed = ref(false)
const adminUser = ref<AdminSessionUser | null>(null)
const isChecking = ref(true)

onMounted(async () => {
  adminUser.value = await fetchAdminSessionUser()
  isChecking.value = false
})

function handleNavigate(route: string) {
  if (route === router.currentRoute.value.path) return
  router.push(route)
}
</script>

<style scoped>
.admin-shell {
  display: flex;
  min-height: 100vh;
  background: #F9FAFB;
  font-family: 'Inter', -apple-system, BlinkMacSystemFont, sans-serif;
}

.admin-main {
  flex: 1;
  display: flex;
  flex-direction: column;
  min-width: 0;
  overflow: hidden;
}

.admin-content {
  flex: 1;
  overflow-y: auto;
  padding: 24px;
}

.access-denied {
  flex: 1;
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  text-align: center;
  padding: 24px;
  color: #374151;
}

.access-denied h2 {
  font-size: 20px;
  font-weight: 700;
  margin-bottom: 8px;
  color: #DC2626;
}

.access-denied p {
  font-size: 14px;
  color: #6B7280;
  max-width: 360px;
}

.admin-loading {
  flex: 1;
  display: flex;
  align-items: center;
  justify-content: center;
  color: #6B7280;
  font-size: 14px;
}
</style>