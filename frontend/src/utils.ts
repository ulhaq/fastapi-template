import { isEmpty } from "lodash";

type SortParam = {
  key: string;
  order: "asc" | "desc";
};
const createSorts = (params: SortParam[] | null | undefined): string | null => {
  if (isEmpty(params) || !params) return null;

  return params
    .map(({ key, order }) => (order === "desc" ? `-${key}` : key))
    .join(",");
};

const createFilters = (
  params: Record<string, string>,
  value: string | null
): string | null => {
  if (value == null || value === "") {
    return null;
  }

  const filters = Object.fromEntries(
    Object.entries(params).map(([key, operator]) => [
      key,
      { v: [value], op: operator },
    ])
  );

  return JSON.stringify(filters);
};

export default {
  createSorts,
  createFilters,
};
