import { Given, Then, When } from "@badeball/cypress-cucumber-preprocessor";

type Credenciais = { ADMIN_LOGIN: string; ADMIN_PASSWORD: string };

// Nome único por execução: o banco do E2E não é limpo entre cenários.
let nome = "";
const linha = () => cy.contains("[data-cy=produto]", nome);

Given("que estou logado no painel", () => {
  cy.visit("/");
  cy.env<Credenciais>(["ADMIN_LOGIN", "ADMIN_PASSWORD"]).then(({ ADMIN_LOGIN, ADMIN_PASSWORD }) => {
    cy.get("input[name=login]").type(ADMIN_LOGIN);
    cy.get("input[name=senha]").type(ADMIN_PASSWORD, { log: false });
    cy.contains("button", "Entrar").click();
  });
  cy.get("[data-cy=form-produto]").should("be.visible");
});

When("cadastro o produto com nome único, unidade {string} e preço {string}", (unidade: string, preco: string) => {
  nome = `teste-${Date.now()}`;
  cy.get("#p-nome").type(nome);
  cy.get("#p-unidade").clear().type(unidade);
  cy.get("#p-preco").type(preco);
  cy.contains("button", "Cadastrar").click();
});

When("altero o preço do produto para {string}", (preco: string) => {
  linha().find("input[name=preco]").clear().type(preco);
  linha().contains("button", "Salvar").click();
});

When("inativo o produto", () => {
  linha().contains("button", "Inativar").click();
});

Then("o produto aparece na lista", () => {
  linha().should("exist");
});

Then("o preço do produto é {string}", (preco: string) => {
  linha()
    .find("input[name=preco]")
    .invoke("val")
    .should((v) => expect(Number(v)).to.eq(Number(preco)));
});

Then("o produto aparece como inativo", () => {
  linha().should("contain", "Inativo");
});
