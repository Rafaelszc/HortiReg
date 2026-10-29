import { Given, Then, When } from "@badeball/cypress-cucumber-preprocessor";

type Credenciais = { ADMIN_LOGIN: string; ADMIN_PASSWORD: string };

function entrar(senhaErrada = false) {
  cy.env<Credenciais>(["ADMIN_LOGIN", "ADMIN_PASSWORD"]).then(({ ADMIN_LOGIN, ADMIN_PASSWORD }) => {
    cy.get("input[name=login]").type(ADMIN_LOGIN);
    cy.get("input[name=senha]").type(senhaErrada ? "senha-errada-xyz" : ADMIN_PASSWORD, {
      log: false,
    });
    cy.contains("button", "Entrar").click();
  });
}

Given("que estou na tela de login", () => {
  cy.visit("/");
});

When("informo o login e a senha corretos", () => entrar());

When("informo uma senha incorreta", () => entrar(true));

Then("vejo o painel", () => {
  cy.env<Credenciais>(["ADMIN_LOGIN"]).then(({ ADMIN_LOGIN }) => {
    cy.get("[data-cy=boas-vindas]").should("contain", ADMIN_LOGIN);
  });
});

Then("vejo a mensagem {string}", (msg: string) => {
  cy.get("[data-cy=erro]").should("have.text", msg);
});
