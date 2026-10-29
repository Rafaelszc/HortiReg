import createBundler from "@bahmutov/cypress-esbuild-preprocessor";
import { addCucumberPreprocessorPlugin } from "@badeball/cypress-cucumber-preprocessor";
import { createEsbuildPlugin } from "@badeball/cypress-cucumber-preprocessor/esbuild";
import { defineConfig } from "cypress";

export default defineConfig({
  e2e: {
    baseUrl: "http://127.0.0.1:5173",
    specPattern: "cypress/e2e/**/*.feature",
    supportFile: false,
    // Cypress 16: filtro de tags é público (expose); credenciais ficam em env (cy.env).
    expose: {
      tags: process.env.TAGS ?? "@smoke and not @wip",
    },
    env: {
      ADMIN_LOGIN: process.env.ADMIN_LOGIN ?? "admin",
      ADMIN_PASSWORD: process.env.ADMIN_PASSWORD ?? "",
    },
    async setupNodeEvents(on, config) {
      await addCucumberPreprocessorPlugin(on, config);
      on(
        "file:preprocessor",
        createBundler({ plugins: [createEsbuildPlugin(config)] }),
      );
      return config;
    },
  },
});
