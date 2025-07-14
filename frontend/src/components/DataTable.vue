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
    :items-per-page-options="[10, 25, 50, 100, 500]"
    @update:options="emitOptions"
    class="border"
  >
    <template #top>
      <slot name="top" />
    </template>

    <template #item="{ item, index }">
      <slot name="item" :item="item" :index="index" />
    </template>

    <template #no-data>
      <slot name="no-data">No data available</slot>
    </template>
  </v-data-table-server>
</template>

<script setup>
defineProps({
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
