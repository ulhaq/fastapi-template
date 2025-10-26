import { da } from 'vuetify/locale'

export default {
  $vuetify: {
    ...da,
  },
  rules: {
    required: 'Dette felt er påkrævet',
    email: 'E-mailen er ugyldig',
    min: 'Mindst {length} tegn er påkrævet',
  },
  errors: {
    common: 'Noget gik galt',
    api: {
      login_failed: 'Ugyldig email or adgangskode',
      signature_expired: 'Linket er udløbet',
      signature_invalid: 'Linket er ugyldigt',
      resource_already_exists: 'Den findes allerede',
      resource_not_found: 'Den findes ikke',
      email_already_exists: 'Den angivne e-mail findes allerede',
      value_error: '{field} er ugyldig',
      string_too_short: '{field} skal være mindst {min_length} tegn',
    },
    fields: {
      'body,name': '@:common.name',
      'body,email': '@:common.email',
      'body,password': '@:common.password',
      'body,description': '@:common.description',
    },
  },
  common: {
    name: 'Navn',
    email: 'E-mail',
    password: 'Adgangskode',
    description: 'Beskrivelse',
    createdAt: 'Oprettet den',
    updatedAt: 'Opdateret den',
    actions: 'Handlinger',
    search: 'Søg (Ctrl+K eller /)',
    close: 'Luk',
    cancel: 'Annuller',
    confirm: 'Bekræft',
    save: 'Gem',
    submit: 'Indsend',
  },
  menuBar: {
    index: 'Hjem',
    users: 'Brugere',
    roles: 'Roller',
    permissions: 'Tilladelser',
  },
  login: {
    form: {
      title: 'Login',
      submit: 'Login',
      newAccount: 'Ny konto',
      resetPassword: 'Nulstil adgangskode',
    },
  },
  register: {
    form: {
      title: 'Opret en konto',
      submit: 'Opret konto',
      login: 'Login',
      resetPassword: 'Nulstil adgangskode',
    },
  },
  reset: {
    form: {
      requestTitle: 'Nulstil din adgangskode',
      resetTitle: 'Vælg en ny adgangskode',
      update: 'Opdater adgangskode',
      requestSuccess: 'Hvis der findes en konto med denne e-mail, er der sendt et link for nulstilling af adgangskoden',
      resetSuccess: 'Din adgangskode er blevet nulstillet',
      newAccount: 'Ny konto',
      login: 'Login',
    },
  },
  users: {
    title: 'Brugere',
  },
  roles: {
    title: 'Roller',
    add: 'Tilføj ny rolle',
    form: {
      addTitle: 'Tilføj ny rolle',
      editTitle: 'Rediger rolle',
      permissionAssignmentTitle: 'Tildel tilladelser til {role}',
      saveAndNext: 'Gem og tildel tilladelser',
      assignPermissionsToRole: 'Tildel tilladelser',
      addSuccess: 'Rollen er blev tilføjet',
      updateSuccess: 'Rollen er blev opdateret',
      deleteSuccess: 'Rollen er blev slettet',
      assignedPermissionsSuccess: 'Tilladelser er blev tildelt rollen',
    },
    permissionForm: {
      title: 'Administrér tilladelser',
      permissions: 'Tilladelser',
    },
  },
  permissions: {
    title: 'Tilladelser',
    add: 'Tilføj ny tilladelse',
    form: {
      addTitle: 'Tilføj ny tilladelse',
      editTitle: 'Rediger tilladelse',
      addSuccess: 'Tilladelsen er blev tilføjet',
      updateSuccess: 'Tilladelsen er blev opdateret',
      deleteSuccess: 'Tilladelsen er blev slettet',
    },
  },
}
