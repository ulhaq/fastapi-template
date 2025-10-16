import { en } from 'vuetify/locale'

export default {
  $vuetify: {
    ...en,
  },
  rules: {
    required: 'This field is required',
    email: 'Email is invalid',
    min: 'Minimum {length} characters are required',
  },
  errors: {
    common: 'Something went wrong',
    invalidCredentials: 'Credentials are invalid',
    loginFailed: 'Login failed',
  },
  common: {
    name: 'Name',
    email: 'Email',
    password: 'Password',
    description: 'Description',
    createdAt: 'Created at',
    updatedAt: 'Updated at',
    actions: 'Actions',
    search: 'Search (Ctrl+K or /)',
    close: 'Close',
    cancel: 'Cancel',
    confirm: 'Confirm',
    save: 'Save',
    submit: 'Submit',
  },
  menuBar: {
    index: 'Home',
    users: 'Users',
    roles: 'Roles',
    permissions: 'Permissions',
  },
  login: {
    form: {
      title: 'Login',
      submit: 'Login',
      newAccount: 'New account',
      resetPassword: 'Reset password',
    },
  },
  register: {
    form: {
      title: 'Create an account',
      submit: 'Create account',
    },
  },
  reset: {
    form: {
      requestTitle: 'Request password reset',
      resetTitle: 'Choose a new password',
      update: 'Update password',
      requestSuccess: 'If an account with that email exists, a password reset link has been sent',
      resetSuccess: 'Your password has been reset successfully',
      newAccount: 'New account',
      login: 'Login',
    },
  },
  users: {
    title: 'Users',
  },
  roles: {
    title: 'Roles',
    add: 'Add new role',
    form: {
      addTitle: 'Add new role',
      editTitle: 'Edit role',
      permissionAssignmentTitle: 'Assign permissions to {role}',
      saveAndNext: 'Save & assign permissions',
      assignPermissionsToRole: 'Assign permissions',
      addSuccess: 'Role was added successfully',
      updateSuccess: 'Role was updated successfully',
      deleteSuccess: 'Role was deleted successfully',
      assignedPermissionsSuccess:
        'Permissions assigned to the role successfully',
    },
    permissionForm: {
      title: 'Manage permissions',
      permissions: 'Permissions',
    },
  },
  permissions: {
    title: 'Permissions',
    add: 'Add new Permission',
    form: {
      addTitle: 'Add new Permission',
      editTitle: 'Edit Permission',
      addSuccess: 'Permission was added successfully',
      updateSuccess: 'Permission was updated successfully',
      deleteSuccess: 'Permission was deleted successfully',
    },
  },
}
