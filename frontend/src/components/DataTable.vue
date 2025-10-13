<template>
  <v-row>
    <v-col>
      <v-toolbar color="transparent">
        <slot name="toolbar.search">
          <search-bar v-model="search" />
        </slot>
        <v-spacer v-if="props.toolbarSpacer" />
        <slot name="toolbar.action" />
      </v-toolbar>
    </v-col>
  </v-row>
  <v-row>
    <v-col>
      <v-data-table-server
        v-model="modelValue"
        class="elevation-2 rounded"
        :headers="headers"
        :items="items"
        :items-length="totalItems"
        :items-per-page="options.itemsPerPage"
        :items-per-page-options="[10, 25, 50, 100]"
        :loading="loading"
        multi-sort
        :page="options.page"
        :show-select="showSelect"
        :sort-by="options.sortBy"
        :sort-desc="options.sortDesc"
        @update:options="emitOptions"
      >
        <!-- <template #loading>
          <v-skeleton-loader type="table-row@10" />
        </template> -->

        <template
          v-for="header in headers"
          :key="header.key"
          #[`item.${header.key}`]="{ item }"
        >
          <slot :item="item" :name="`item.${header.key}`">
            <span v-html="utils.highlightSearchTerm(search, item[header.key])" />
          </slot>
        </template>
      </v-data-table-server>
    </v-col>
  </v-row>
</template>

<script setup>
  import debounce from 'lodash/debounce'
  import utils from '@/utils'

  const props = defineProps({
    toolbarSpacer: {
      type: Boolean,
      default: true,
    },
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
    itemValue: {
      type: String,
      required: false,
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
      type: Boolean,
      default: false,
    },
  })

  const emit = defineEmits(['update:options'])

  const modelValue = defineModel()

  const search = ref('')

  function emitOptions (newOptions) {
    emit('update:options', {
      ...props.options,
      ...newOptions,
      search: search.value,
    })
  }

  watch(
    search,
    debounce(() => {
      emitOptions({ ...props.options, page: 1 })
    }, 300),
  )
</script>
