# Documentos de Qualidade - HortiReg

**Projeto:** HortiReg · Gerência de Projetos (UEPB, 2026.2)  
**QA da Release 1:** Julio Araújo  
**QA da Release 2:** Rafael  

## Matriz de Documentos de Qualidade

| Documento | Arquivo / Referência | Card no Jira | Responsável | Status |
|---|---|:---:|:---:|:---:|
| Plano de Qualidade | `docs/planos/Plano_de_Qualidade_HortiReg_v1.1.xlsx` | HORTI-QA-01 | Julio Araújo (R1) / Rafael (R2) | Resultados R1 e R2 preenchidos (25/11) |
| Plano de Teste | `docs/planos/Plano-de-Teste_HortiReg_v1.1.docx` | HORTI-QA-02 | Julio Araújo (R1) / Rafael (R2) | v1.1 |
| Análise de Riscos Baseada em Defeitos | `GP_RiscoBaseadoDefeitos.xlsx` | HORTI-QA-03 | Julio Araújo | [Mapeado / A Preencher] |
| Relatório de Bugs da Sprint 1 | `Bugs_Sprint1_HortiReg.txt` | HORTI-QA-04 | Julio Araújo | Disponível |
| Casos de Teste da Sprint 1 | `Casos_de_Teste_Sprint1_HortiReg.txt` | HORTI-QA-05 | Julio Araújo | Histórico (12/11) |
| Casos de teste e rastreabilidade (vigente) | `casos-de-teste.md` | — | Rafael | Atualizado em 26/11 (US-11, US-12, Telegram) |
| Registro de bugs da R2 (BUG-01 a BUG-09) | `Bugs_Sprint1_HortiReg.txt` | SCRUM-71 a 76, 83 a 85 | Rafael | Atualizado em 26/11 |
| Relatório de qualidade da R2 | `docs/releases/release-2/relatorio-qualidade.md` | — | Rafael | Fechado em 26/11 (regressão final em `d638ac0`, métricas e riscos) |
| DoD (Sprint e Release) | `docs/planos/Definition_of_Done_HortiReg_v1.1.xlsx` | — | QA verifica, PO aceita | Sprints 1 a 3 e Release 2 (itens do QA) |

---

## Observações e Mapeamento
- Os testes automatizados encontram-se versionados em `backend/tests/` (Pytest com BDD em `backend/tests/features/`) e `frontend/cypress/e2e/`.
- Os arquivos `.xlsx` e `.docx` são mantidos como templates e planilhas vivas preenchidas pelo responsável de QA de cada release.
