import { da } from 'vuetify/locale'

export default {
  $vuetify: {
    ...da,
  },
  rules: {
    matchesField: 'Dette felt og {targetLabel} skal være ens',
    confirmPassword: 'Adgangskoderne stemmer ikke overens',
  },
  errors: {
    common: 'Noget gik galt',
    api: {
      login_failed: 'Ugyldig email eller adgangskode',
      signature_expired: 'Linket er udløbet',
      signature_invalid: 'Linket er ugyldigt',
      resource_already_exists: 'Den findes allerede',
      resource_not_found: 'Den findes ikke',
      email_already_exists: 'Den angivne email er allerede i brug',
      value_error: '{field} er ugyldig',
      int_parsing: '{field} er ugyldig',
      list_type: '{field} skal være en liste',
      string_too_short: '{field} skal mindst være {min_length} tegn',
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
    clear: 'Ryd',
    clearAll: 'Ryd Alle',
    confirm: 'Bekræft',
    save: 'Gem',
    submit: 'Indsend',
  },
  messagePanel: {
    title: 'Beskedpanel',
    show: 'Vis beskedpanel',
    hide: 'Skjul beskedpanel',
  },
  menuBar: {
    index: 'Hjem',
    users: 'Brugere',
    roles: 'Roller',
    permissions: 'Tilladelser',
    settings: 'Indstillinger',
    languages: 'Sprog',
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
      requestSuccess: 'Hvis en konto med denne email findes, er et nulstillingslink sendt',
      resetSuccess: 'Din adgangskode er nulstillet',
      newAccount: 'Ny konto',
      login: 'Login',
    },
  },
  settings: {
    title: 'Indstillinger',
    tab1: {
      name: 'Profil',
      profileForm: {
        title: 'Profil',
        profileSuccess: 'Profil opdateret',
      },
    },
    tab2: {
      name: 'Sikkerhed',
      passwordForm: {
        title: 'Ny adgangskode',
        currentPassword: 'Nuværende adgangskode',
        newPassword: 'Ny adgangskode',
        confirmPassword: 'Bekræft adgangskode',
        passwordSuccess: 'Adgangskode ændret',
      },
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
      addSuccess: 'Rollen er tilføjet',
      updateSuccess: 'Rollen er opdateret',
      deleteSuccess: 'Rollen er slettet',
      assignedPermissionsSuccess: 'Tilladelserne er tildelt rollen',
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
      addSuccess: 'Tilladelsen er tilføjet',
      updateSuccess: 'Tilladelsen er opdateret',
      deleteSuccess: 'Tilladelsen er slettet',
    },
  },
}
