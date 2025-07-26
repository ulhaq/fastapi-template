<template>
  <v-data-table-server
    :headers="headers"
    :items="items"
    :items-length="totalItems"
    :loading="loading"
    :items-per-page="options.itemsPerPage"
    :page="options.page"
    :sort-by="options.sortBy"
    :sort-desc="options.sortDesc"
    multi-sort
    :items-per-page-options="[10, 25, 50, 100]"
    @update:options="emitOptions"
    class="elevation-2 rounded"
  >
    <template #item.actions="{ item }">
      <slot name="row-actions" :item="item"> </slot>
    </template>
  </v-data-table-server>
</template>

<script setup>
const props = defineProps({
  headers: {
    type: Array,
    required: true,
  },
  items: {
    type: Array,
    required: true,
  },
  totalItems: {
    type: Number,
    required: true,
  },
  loading: {
    type: Boolean,
    default: false,
  },
  options: {
    type: Object,
    required: true,
  },
});

const emit = defineEmits(["update:options"]);

function emitOptions(newOptions) {
  emit("update:options", newOptions);
}
</script>
