import { Then, When } from "@badeball/cypress-cucumber-preprocessor";

When("escolho ver {string} os pedidos", (filtro: string) => {
  cy.contains(".segmentado button", filtro).click().should("have.attr", "aria-pressed", "true");
});

Then("vejo {string}", (texto: string) => {
  cy.contains("h2", texto).should("be.visible");
});
