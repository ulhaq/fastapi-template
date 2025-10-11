<template>
  <v-row>
    <v-col>
      <v-toolbar color="transparent">
        <slot name="toolbar-search">
          <search-bar v-model="search" />
        </slot>
        <v-spacer />
        <slot name="toolbar-action"></slot>
      </v-toolbar>
    </v-col>
  </v-row>
  <v-row>
    <v-col>
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
        :show-select="showSelect"
        :items-per-page-options="[10, 25, 50, 100]"
        class="elevation-2 rounded"
        @update:options="emitOptions"
      >
        <template #item.actions="{ item }">
          <slot name="row-actions" :item="item"></slot>
        </template>
      </v-data-table-server>
    </v-col>
  </v-row>
</template>

<script setup>
import debounce from "lodash/debounce";

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
  showSelect: {
    type: Object,
    required: true,
  },
});

const emit = defineEmits(["update:options"]);

const search = ref("");

function emitOptions(newOptions) {
  emit("update:options", {
    ...props.options,
    ...newOptions,
    search: search.value,
  });
}

watch(
  search,
  debounce(() => {
    emitOptions({ ...props.options, page: 1 });
  }, 300)
);
</script>
