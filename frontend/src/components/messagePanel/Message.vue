<template>
  <v-alert
    :icon="false"
    :text="props.message.text"
    :type="props.message.type"
    rounded="0"
    @click:close="messageStore.remove(props.message)"
  >
    <template #close>
      <v-progress-circular v-if="props.message.timeout" :model-value="progress">
        <v-btn
          color="white"
          icon="mdi-close"
          size="small"
          :title="t('common.clear')"
          @click="messageStore.remove(props.message)"
        />
      </v-progress-circular>
      <v-btn
        v-else
        color="white"
        icon="mdi-close"
        size="small"
        :title="t('common.clear')"
        @click="messageStore.remove(props.message)"
      />
    </template>
  </v-alert>
</template>

<script setup>
import { ref } from 'vue'
import { useI18n } from 'vue-i18n'
import { useMessageStore } from '@/stores/message'

const { t } = useI18n()

const props = defineProps({
  message: {
    type: Object,
    required: true,
  },
})

const messageStore = useMessageStore()

const progress = ref(0)

let interval = null

onMounted(() => {
  interval = setInterval(() => {
    progress.value = Math.min(
      ((Date.now() - props.message.time) / props.message.timeout) * 100,
      100,
    )
  }, 100)
})

onBeforeUnmount(() => clearInterval(interval))
</script>
