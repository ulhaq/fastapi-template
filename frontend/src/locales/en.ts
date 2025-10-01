import { en } from "vuetify/locale";

export default {
  $vuetify: {
    ...en,
  },
  rules: {
    required: "This field is required",
    email: "Email is invalid",
  },
  errors: {
    common: "Something went wrong",
    invalidCredentials: "Credentials are invalid",
    loginFailed: "Login failed",
  },
  common: {
    name: "Name",
    email: "Email",
    password: "Password",
    description: "Description",
    createdAt: "Created at",
    updatedAt: "Updated at",
    actions: "Actions",
    search: "Search",
    close: "Close",
    cancel: "Cancel",
    save: "Save",
    addSuccess: "{name} added successfully",
    updateSuccess: "{name} updated successfully",
    deleteSuccess: "{name} deleted successfully",
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
      submit: "Login",
      newAccount: "New account",
      resetPassword: "Reset password",
    },
  },
  register: {
    form: {
      title: "Create an account",
      submit: "Create account",
    },
  },
  reset: {
    form: {
      title: "Request password reset",
      submit: "Submit",
      newAccount: "New account",
      login: "Login",
    },
  },
  users: {
    title: "Users",
  },
  roles: {
    title: "Roles",
    add: "Add new role",
    addForm: {
      title: "Add new role",
      saveAndNext: "Save & assign permissions",
      assignPermissionsToRole: "Assign permissions",
      assignedPermissionsSuccess:
        "Permissions assigned to the role successfully",
    },
    editForm: {
      title: "Edit role",
    },
    permissionForm: {
      title: "Manage permissions",
      permissions: "Permissions",
    },
  },
  permissions: {
    title: "Permissions",
    add: "Add new permission",
    addForm: {
      title: "Add new permission",
    },
    editForm: {
      title: "Edit permission",
    },
  },
};
