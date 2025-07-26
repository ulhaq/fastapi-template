import { en } from "vuetify/locale";

export default {
  $vuetify: {
    ...en,
  },
  rules: {
    required: "This field is required",
  },
  common: {
    table: {
      search: "Search",
      createdAt: "Created at",
      updatedAt: "Updated at",
      actions: "Actions",
    },
    error: "Something went wrong",
    close: "Close",
    cancel: "Cancel",
    save: "Save",
  },
  menuBar: {
    index: "Home",
    users: "Users",
    roles: "Roles",
    permissions: "Permissions",
  },
  login: {
    form: {
      title: "Login",
      username: "Email",
      password: "Password",
      submit: "Login",
      newAccount: "New account",
      resetPassword: "Reset password",
    },
    error: {
      invalid: "Username or password is incorrect",
      failed: "Login failed",
    },
  },
  users: {
    title: "Users",
    table: {
      name: "Name",
      description: "Description",
    },
  },
  roles: {
    title: "Roles",
    add: "Add new role",
    added: "Role added successfully",
    assignedPermissions: "Permissions assigned to the role successfully",
    managePermissions: "Manage permissions",
    permissionsUpdated: "Permissions updated successfully",
    addForm: {
      title: "Add new role",
      name: "Name",
      description: "Description",
      saveAndNext: "Save & assign permissions",
      assignPermissionsToRole: "Assign permissions",
    },
    editForm: {
      title: "Add new role",
      name: "Name",
      description: "Description",
      saveAndNext: "Save & assign permissions",
      assignPermissionsToRole: "Assign permissions",
    },
    table: {
      name: "Name",
      description: "Description",
    },
  },
  permissions: {
    title: "Permissions",
    add: "Add new permission",
    added: "Permission added successfully",
    addForm: {
      title: "Add new permission",
      name: "Name",
      description: "Description",
    },
    table: {
      name: "Name",
      description: "Description",
    },
  },
};
