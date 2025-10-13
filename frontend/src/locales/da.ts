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
    invalidCredentials: 'Legitimationsoplysningerne er ugyldige',
    loginFailed: 'Login mislykkedes',
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
    },
  },
  reset: {
    form: {
      requestTtitle: 'Anmod om nulstilling af adgangskode',
      resetTitle: 'Vælg en ny adgangskode',
      submit: 'Indsend',
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
      saveAndNext: 'Gem og tildel tilladelser',
      assignPermissionsToRole: 'Tildel tilladelser',
      addSuccess: 'Rollen blev tilføjet succesfuldt',
      updateSuccess: 'Rollen blev opdateret succesfuldt',
      deleteSuccess: 'Rollen blev slettet succesfuldt',
      assignedPermissionsSuccess: 'Tilladelser blev tildelt rollen succesfuldt',
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
      addSuccess: 'Tilladelsen blev tilføjet succesfuldt',
      updateSuccess: 'Tilladelsen blev opdateret succesfuldt',
      deleteSuccess: 'Tilladelsen blev slettet succesfuldt',
    },
  },
}
