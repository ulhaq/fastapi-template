import axios from "@/apis/base";

const endpoint = "roles";

export default {
  async getAll(params?: any) {
    params = params || {};

    if (params.sort) {
      params.sort = params.sort
        .map((sort: any) => (sort.order === "desc" ? `-${sort.key}` : sort.key))
        .join(",");
    }
    const response = await axios.get(endpoint, { params });
    return response.data;
  },

  async getById(id: string | number) {
    const response = await axios.get(`${endpoint}/${id}`);
    return response.data;
  },

  async create(data: object) {
    const response = await axios.post(endpoint, data);
    return response.data;
  },

  async updateById(id: string | number, data: object) {
    const response = await axios.put(`${endpoint}/${id}`, data);
    return response.data;
  },

  async deleteById(id: string | number) {
    await axios.delete(`${endpoint}/${id}`);
  },

  async assignPermissions(roleId: Number, permissionIds: Array<Number>) {
    const response = await axios.post(`${endpoint}/${roleId}/permissions`, {
      permission_ids: permissionIds,
    });
    return response.data;
  },
};
