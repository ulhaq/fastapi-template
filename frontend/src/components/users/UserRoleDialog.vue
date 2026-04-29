<template>
  <Dialog :open="open" @update:open="$emit('update:open', $event)">
    <DialogContent class="sm:max-w-md">
      <DialogHeader>
        <DialogTitle>{{ $t("users.roleDialog.title") }}</DialogTitle>
        <DialogDescription>{{
          $t("users.roleDialog.description", { name: user?.name })
        }}</DialogDescription>
      </DialogHeader>

      <div v-if="loadingRoles" class="py-4 space-y-2">
        <Skeleton v-for="n in 3" :key="n" class="h-10 w-full" />
      </div>
      <div v-else class="space-y-2 max-h-64 overflow-y-auto py-1">
        <div
          v-for="role in availableRoles"
          :key="role.id"
          class="flex items-center gap-3 px-3 py-2 rounded-md hover:bg-muted cursor-pointer"
          @click="toggleRole(role.id)"
        >
          <Checkbox
            :model-value="selectedIds.includes(role.id)"
            @click.stop="toggleRole(role.id)"
          />
          <div>
            <p class="text-sm font-medium">{{ role.name }}</p>
            <p v-if="role.description" class="text-xs text-muted-foreground">
              {{ role.description }}
            </p>
          </div>
        </div>
        <EmptyState
          v-if="!availableRoles.length"
          :title="$t('users.roleDialog.noRoles')"
          :description="$t('users.roleDialog.createRolesFirst')"
        />
      </div>

      <DialogFooter>
        <Button
          variant="outline"
          @click="$emit('update:open', false)"
          :disabled="isLoading"
          >{{ $t("common.cancel") }}</Button
        >
        <Button @click="onSave" :disabled="isLoading">
          <Loader2 v-if="isLoading" class="w-4 h-4 mr-2 animate-spin" />
          {{ $t("common.save") }}
        </Button>
      </DialogFooter>
    </DialogContent>
  </Dialog>
</template>

<script setup lang="ts">
import { ref, watch } from "vue";
import { useI18n } from "vue-i18n";
import { Loader2 } from "lucide-vue-next";
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogFooter,
  DialogHeader,
  DialogTitle,
} from "@/components/ui/dialog";
import { Button } from "@/components/ui/button";
import { Checkbox } from "@/components/ui/checkbox";
import { Skeleton } from "@/components/ui/skeleton";
import EmptyState from "@/components/common/EmptyState.vue";
import { usersApi } from "@/api/users";
import { rolesApi } from "@/api/roles";
import { PAGE_SIZE } from "@/constants";
import type { UserOut, RoleOut } from "@/types";
import { useToast } from "@/composables/useToast";

const props = defineProps<{ open: boolean; user?: UserOut | null }>();
const emit = defineEmits<{ "update:open": [boolean]; saved: [] }>();

const { toast } = useToast();
const { t } = useI18n();
const availableRoles = ref<RoleOut[]>([]);
const selectedIds = ref<number[]>([]);
const loadingRoles = ref(false);
const isLoading = ref(false);

watch(
  () => props.open,
  async (open) => {
    if (!open || !props.user) return;
    selectedIds.value = props.user.roles.map((r) => r.id);
    loadingRoles.value = true;
    try {
      const { data } = await rolesApi.list({ page_size: PAGE_SIZE });
      availableRoles.value = data.items;
    } finally {
      loadingRoles.value = false;
    }
  },
);

function toggleRole(id: number) {
  const idx = selectedIds.value.indexOf(id);
  if (idx >= 0) selectedIds.value.splice(idx, 1);
  else selectedIds.value.push(id);
}

async function onSave() {
  if (!props.user) return;
  isLoading.value = true;
  try {
    await usersApi.setRoles(props.user.id, { role_ids: selectedIds.value });
    emit("update:open", false);
    emit("saved");
    toast({ title: t("users.roleDialog.saved") });
  } catch {
    toast({ title: t("users.roleDialog.saveFailed"), variant: "destructive" });
  } finally {
    isLoading.value = false;
  }
}
</script>
