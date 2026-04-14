<template>
  <div class="min-h-screen bg-background flex">
    <!-- Desktop Sidebar -->
    <aside
      class="hidden lg:flex flex-col w-64 shrink-0 border-r border-sidebar-border bg-sidebar transition-all duration-200"
    >
      <AppSidebar />
    </aside>

    <!-- Main content -->
    <div class="flex-1 flex flex-col min-w-0">
      <AppTopbar />
      <TrialBanner />
      <main class="flex-1 p-6 overflow-auto">
        <slot />
      </main>
    </div>

    <!-- Mobile sidebar -->
    <MobileSidebar />

    <!-- Global confirm dialog -->
    <ConfirmDialog />
  </div>
</template>

<script setup lang="ts">
import AppSidebar from '@/components/layout/AppSidebar.vue'
import AppTopbar from '@/components/layout/AppTopbar.vue'
import MobileSidebar from '@/components/layout/MobileSidebar.vue'
import TrialBanner from '@/components/layout/TrialBanner.vue'
import ConfirmDialog from '@/components/common/ConfirmDialog.vue'
</script>
