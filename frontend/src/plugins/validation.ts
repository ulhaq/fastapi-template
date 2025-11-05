import { createRulesPlugin } from 'vuetify/labs/rules'
import i18n from '@/plugins/i18n'
import vuetify from '@/plugins/vuetify'

export default createRulesPlugin(
  {
    aliases: {
      matchesField: (targetValue: any, targetLabel: any, err?: any) => {
        return (v: any) =>
          v === targetValue ||
          err ||
          i18n.global.t('rules.matchesField', {
            targetLabel,
          })
      },
    },
  },
  vuetify.locale,
)
