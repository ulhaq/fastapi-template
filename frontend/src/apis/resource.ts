import axios from "@/apis/base";

export async function getAll(endpoint: string, params?: any) {
  params = params || {};

  if (params.sort) {
    params.sort = params.sort
      .map((sort: any) => (sort.order === "desc" ? `-${sort.key}` : sort.key))
      .join(",");
  }

  const response = await axios.get(endpoint, { params });
  return response.data;
}

export async function getById(endpoint: string, id: string | number) {
  const response = await axios.get(`${endpoint}/${id}`);
  return response.data;
}

export async function create(endpoint: string, data: object) {
  const response = await axios.post(endpoint, data);
  return response.data;
}

export async function updateById(
  endpoint: string,
  id: string | number,
  data: object
) {
  const response = await axios.put(`${endpoint}/${id}`, data);
  return response.data;
}

export async function deleteById(endpoint: string, id: string | number) {
  await axios.delete(`${endpoint}/${id}`);
}
