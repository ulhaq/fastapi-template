import { da } from "vuetify/locale";

export default {
  $vuetify: {
    ...da,
  },
  common: {
    table: {
      search: "Søg",
      createdAt: "Oprettet den",
      updatedAt: "Opdateret den",
    },
    close: "Luk",
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
    form: {
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
    form: {
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
