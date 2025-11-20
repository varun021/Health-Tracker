"use client";

import * as React from "react";
import {
  IconCamera,
  IconChartBar,
  IconDashboard,
  IconDatabase,
  IconFileAi,
  IconFileDescription,
  IconFileWord,
  IconFolder,
  IconHelp,
  IconInnerShadowTop,
  IconListDetails,
  IconReport,
  IconSearch,
  IconSettings,
  IconUsers,
  IconStethoscope,
} from "@tabler/icons-react";

import { NavMain } from "@/components/nav-main";
import { NavUser } from "@/components/nav-user";

import {
  Sidebar,
  SidebarContent,
  SidebarFooter,
  SidebarHeader,
  SidebarMenu,
  SidebarMenuButton,
  SidebarMenuItem,
} from "@/components/ui/sidebar";

import MedicalPredictionApp from "./symptom/UserForm";
import ModelReportPage from "./symptom/model-report";
import Analytics from "@/components/symptom/Analytics";
import ReportsPage from "./symptom/Reports";
import ChatAssistant from "./symptom/ChatAssistant";

import { MessageCircle } from "lucide-react";
import { useNavigationStore } from "@/lib/stores/navigation-store";

const navItems = [
  {
    title: "Medical Prediction",
    url: "/medical-prediction",
    icon: IconStethoscope,
    component: MedicalPredictionApp,
  },
  {
    title: "Analytics",
    url: "/analytics",
    icon: IconChartBar,
    component: Analytics,
  },
  {
    title: "Data Library",
    url: "/data",
    icon: IconDatabase,
    component: ModelReportPage,
  },
  {
    title: "Reports",
    url: "/reports",
    icon: IconReport,
    component: ReportsPage,
  },
  {
    title: "Chat Assistant",
    url: "/chat",
    icon: MessageCircle,
    component: ChatAssistant,
  },
];

export function AppSidebar({ user: passedUser = null, ...props }) {
  const { setActiveComponent } = useNavigationStore();
  const userData = passedUser || { name: "User", email: "user@example.com" };

  const handleMenuClick = (item) => {
    // When item has component, set it as active component
    if (item?.component) {
      setActiveComponent(item);
    } else {
      setActiveComponent(null);
    }
  };

  return (
    <Sidebar collapsible="offcanvas" {...props}>
      <SidebarHeader>
        <SidebarMenu>
          <SidebarMenuItem>
            <SidebarMenuButton asChild>
              <a href="/dashboard" className="flex items-center gap-2 px-3 py-2">
                <IconInnerShadowTop className="!size-5" />
                <span className="text-base font-semibold">Health Tracker</span>
              </a>
            </SidebarMenuButton>
          </SidebarMenuItem>
        </SidebarMenu>
      </SidebarHeader>

      <SidebarContent className="h-full overflow-hidden">
        <NavMain items={navItems} onItemClick={handleMenuClick} />
      </SidebarContent>

      <SidebarFooter>
        <NavUser user={userData} />
      </SidebarFooter>
    </Sidebar>
  );
}
