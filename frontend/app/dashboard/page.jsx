"use client"

import ProtectedRoute from '@/components/auth/protected-route'
import { AppSidebar } from "@/components/app-sidebar"
import { SiteHeader } from "@/components/site-header"
import {
  SidebarInset,
  SidebarProvider,
} from "@/components/ui/sidebar"
import { useNavigationStore } from "@/lib/stores/navigation-store"
import useAuthStore from '@/stores/useAuthStore'
import UserForm from '@/components/symptom/UserForm'

export default function Page() {
  const { activeComponent } = useNavigationStore()
  const { user } = useAuthStore()

  return (
    <ProtectedRoute>
      <SidebarProvider
        style={{
          "--sidebar-width": "calc(var(--spacing) * 72)",
          "--header-height": "calc(var(--spacing) * 12)",
        }}
      >
        <AppSidebar variant="inset" user={user} />

        <SidebarInset className="flex flex-col h-full min-h-screen">
          {/* <SiteHeader /> */}

          <main className="flex-1 p-6 overflow-x-hidden">
            {activeComponent ? (
              <activeComponent.component />
            ) : (
              <UserForm />
            )}
          </main>
        </SidebarInset>
      </SidebarProvider>
    </ProtectedRoute>
  )
}
