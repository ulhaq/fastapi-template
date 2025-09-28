import { da } from "vuetify/locale";

export default {
  $vuetify: {
    ...da,
  },
  rules: {
    required: "Dette felt er påkrævet",
  },
  common: {
    table: {
      search: "Søg",
      createdAt: "Oprettet den",
      updatedAt: "Opdateret den",
      actions: "Handlinger",
    },
    error: "Noget gik galt",
    close: "Luk",
    cancel: "Annuller",
    save: "Gem",
  },
  menuBar: {
    index: "Hjem",
    users: "Brugere",
    roles: "Roller",
    permissions: "Tilladelser",
  },
  login: {
    form: {
      title: "Log ind",
      username: "Email",
      password: "Adgangskode",
      submit: "Log ind",
      newAccount: "Ny konto",
      resetPassword: "Nulstil adgangskode",
    },
    error: {
      invalid: "Brugernavn eller adgangskode er forkert",
      failed: "Login mislykkedes",
    },
  },
  register: {
    form: {
      title: "Opret en konto",
      name: "Navn",
      username: "Email",
      password: "Adgangskode",
      submit: "Opret konto",
    },
  },

  users: {
    title: "Brugere",
    table: {
      name: "Navn",
      description: "Beskrivelse",
    },
  },
  roles: {
    title: "Roller",
    add: "Tilføj ny rolle",
    added: "Rollen blev tilføjet",
    assignedPermissions: "Tilladelserne blev tildelt rollen",
    managePermissions: "Administrer tilladelser",
    permissionsUpdated: "Tilladelser opdateret",
    addForm: {
      title: "Tilføj ny rolle",
      name: "Navn",
      description: "Beskrivelse",
      saveAndNext: "Gem og tildel tilladelser",
      assignPermissionsToRole: "Tildel tilladelser",
    },
    table: {
      name: "Navn",
      description: "Beskrivelse",
    },
  },
  permissions: {
    title: "Tilladelser",
    add: "Tilføj ny tilladelse",
    added: "Tilladelsen blev tilføjet",
    addForm: {
      title: "Tilføj ny tilladelse",
      name: "Navn",
      description: "Beskrivelse",
    },
    table: {
      name: "Navn",
      description: "Beskrivelse",
    },
  },
};
