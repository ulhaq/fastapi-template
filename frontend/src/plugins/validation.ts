import i18n from "@/plugins/i18n";

export const validation = {
  required(value: any) {
    let result = true;

    if (value === undefined || value === null) {
      result = false;
    } else if (Array.isArray(value) && value.length === 0) {
      result = false;
    } else {
      result = !!String(value).trim().length;
    }
    return result || i18n.global.t("rules.required");
  },
  email(value: string) {
    if (!value) return true;

    return (
      /^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(value) || i18n.global.t("rules.email")
    );
  },
};
