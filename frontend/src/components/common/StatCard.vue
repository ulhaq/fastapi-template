<template>
  <Card class="hover:shadow-sm transition-shadow">
    <CardContent class="pt-6">
      <div class="flex items-center justify-between">
        <div>
          <p class="text-sm font-medium text-muted-foreground">{{ label }}</p>
          <p class="text-3xl font-bold text-foreground mt-1">
            <span v-if="loading">
              <Skeleton class="h-9 w-16" />
            </span>
            <span v-else>{{ value }}</span>
          </p>
        </div>
        <div class="w-10 h-10 rounded-full flex items-center justify-center" :class="iconBg">
          <component :is="icon" class="w-5 h-5" :class="iconColor" />
        </div>
      </div>
    </CardContent>
  </Card>
</template>

<script setup lang="ts">
import { Card, CardContent } from '@/components/ui/card'
import { Skeleton } from '@/components/ui/skeleton'

defineProps<{
  label: string
  value: string | number
  icon: unknown
  loading?: boolean
  iconBg?: string
  iconColor?: string
}>()
</script>
