export default {
  createFilters(params: Record<string, string>, value: unknown): string | null {
    if (value === null || value === undefined || value === "") {
      return null;
    }

    const filters = Object.fromEntries(
      Object.entries(params).map(([key, operator]) => [
        key,
        { v: [value], op: operator },
      ])
    );

    return JSON.stringify(filters);
  },
};
