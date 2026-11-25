import { Given, Then, When } from "@badeball/cypress-cucumber-preprocessor";

Given(
  "que há um pedido confirmado hoje de {string} com {string} no endereço {string} por {float}",
  (cliente: string, itens: string, endereco: string, valor: number) => {
    const [qtd, unidade, , ...nome] = itens.split(" ");
    cy.intercept("GET", "/pedidos/dia", [
      {
        id: 1,
        cliente,
        telefone: "5583999990000",
        endereco,
        itens: [{ nome: nome.join(" "), quantidade: Number(qtd), unidade }],
        valor,
        status: "CONFIRMADO",
        criado_em: new Date().toISOString(),
      },
    ]).as("pedidosDoDia");
  },
);

Given("que não há pedidos confirmados hoje", () => {
  cy.intercept("GET", "/pedidos/dia", []).as("pedidosDoDia");
});

When("abro {string}", (aba: string) => {
  cy.contains("nav button", aba).click();
  cy.wait("@pedidosDoDia");
});

Then(
  "vejo {int} pedido com cliente {string}, itens {string}, endereço {string}, valor {string} e status {string}",
  (n: number, cliente: string, itens: string, endereco: string, valor: string, status: string) => {
    cy.get("[data-cy=pedido-dia]").should("have.length", n);
    cy.get("[data-cy=pedido-cliente]").should("contain", cliente);
    cy.get("[data-cy=pedido-itens]").should("have.text", itens);
    cy.get("[data-cy=pedido-endereco]").should("have.text", endereco);
    // Intl usa espaço não separável entre "R$" e o número
    cy.get("[data-cy=pedido-valor]").invoke("text").should("eq", valor.replace(" ", " "));
    cy.get("[data-cy=pedido-status]").should("have.text", status);
  },
);

Then("vejo o aviso {string}", (mensagem: string) => {
  cy.get("[data-cy=sem-pedidos]").should("have.text", mensagem);
});
