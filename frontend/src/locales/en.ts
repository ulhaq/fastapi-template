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
    api: {
      login_failed: 'Invalid email or password',
      signature_expired: 'The link has expired',
      signature_invalid: 'The link is invalid',
      resource_already_exists: 'It already exists',
      resource_not_found: 'It doesn\'t exist',
      email_already_exists: 'The provided email already exists',
      value_error: '{field} is invalid',
      string_too_short: '{field} must be at least {min_length} character(s)',
    },
    fields: {
      'body,name': '@:common.name',
      'body,email': '@:common.email',
      'body,password': '@:common.password',
      'body,description': '@:common.description',
    },
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
      login: 'Login',
      resetPassword: 'Reset password',
    },
  },
  reset: {
    form: {
      requestTitle: 'Reset your password',
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
      addSuccess: 'Role has been added',
      updateSuccess: 'Role has been updated',
      deleteSuccess: 'Role has been deleted',
      assignedPermissionsSuccess:
        'Permissions have been assigned to the role',
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
      addSuccess: 'Permission has been added',
      updateSuccess: 'Permission has been updated',
      deleteSuccess: 'Permission has been deleted',
    },
  },
}
