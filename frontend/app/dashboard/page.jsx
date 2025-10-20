"use client"

import ProtectedRoute from '@/components/auth/protected-route'
import { AppSidebar } from "@/components/app-sidebar"
import { ChartAreaInteractive } from "@/components/chart-area-interactive"
import { SectionCards } from "@/components/section-cards"
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
        style={
          {
            "--sidebar-width": "calc(var(--spacing) * 72)",
            "--header-height": "calc(var(--spacing) * 12)"
          }
        }>
        <AppSidebar variant="inset" user={user} />
        <SidebarInset>
          <SiteHeader />
          <div className="flex flex-1 flex-col">
            {activeComponent ? (
              <div className="flex-1 p-6">
                <activeComponent.component />
              </div>
            ) : (
              <div className="@container/main flex flex-1 flex-col gap-2">
                {/* <div className="flex flex-col gap-4 py-4 md:gap-6 md:py-6">
                  <SectionCards />
                  <div className="px-4 lg:px-6">
                    <ChartAreaInteractive />
                  </div>
                </div> */}

                <div className="flex-1 p-6">
                  <UserForm />
                </div>
              </div>
            )}
          </div>
        </SidebarInset>
      </SidebarProvider>
    </ProtectedRoute>
  )
}
