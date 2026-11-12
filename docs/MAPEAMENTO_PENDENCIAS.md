# Mapeamento de Estrutura e Pendências - HortiReg

Este documento consolida o mapeamento de toda a estrutura documental do projeto **HortiReg**, indicando o que já foi configurado e o que resta pendente para modificação ou adição pela equipe.

---

## 1. O que foi Configurado e Padronizado

### 📁 Pasta `docs/sm/` (Scrum Master)
- **`acordos-de-trabalho.txt`**:
  - Nomes atualizados: **Nidlan Hendell**, **Rafael** e **Julio Araújo**.
  - **Nidlan Hendell** definido como Scrum Master da Release 2.
  - Pontos 1 a 4 mantidos e reestilizados com layout limpo e padronizado.
  - **Ponto 5 (Matriz de Papéis por Release):**
    - **R1:** Nidlan (PO), Rafael (DevOps e SM), Julio (QA).
    - **R2:** Nidlan (SM), Julio (PO e DevOps), Rafael (QA).
    - **R3:** Rafael (PO e DevOps), Julio (SM), Nidlan (QA).
    - **R4:** Nidlan (PO e DevOps), Rafael (SM), Julio (QA).
    - *Regra atendida: PO e DevOps mantidos juntos da R2 em diante e todos atuam como Dev Team.*
  - **Ponto 6 (Termo de Acordo):** Registrado com a concordância dos três membros.
  - **`secao-README-papeis.txt`**: Snippet em Markdown pronto para integração com a documentação geral do repositório.
- **`calendario-cerimonias.txt`**:
  - Dados pessoais e referências a projetos antigos removidos.
  - Estilo reestruturado em tabela moderna com todos os horários e cerimônias propostos mantidos.
- **Arquivos omitidos (conforme solicitação):**
  - `registro-de-impedimentos.txt` e `registro-de-riscos.txt` **não foram implementados** neste momento (ficarão para uma etapa posterior).

### 📁 Pasta `docs/sm/sprints/sprint-1/`
- **`registro-dailies.txt`**:
  - Inclusão das dailies solicitadas com presença de toda a equipe (Nidlan Hendell, Rafael, Julio Araújo):
    - **03/11/2026**: Pauta centrada na **Correção das pendências**.
    - **05/11/2026**: Pauta de **Acompanhamento de cada um** (status individual).
  - Rastreabilidade com o impedimento IMP-01 (sobrecarga externa do período avaliativo).
- **`registro-de-impedimentos.txt`**:
  - Implementado formalmente dentro da pasta da sprint registrando o **IMP-01** (restrição de capacidade temporária entre 02/11 e 12/11 devido ao encerramento de unidade acadêmica), com causas, impactos na velocidade e ações de contorno do Scrum Master e time.
- **Atas e métricas:**
  - `ata-planning.txt`: Adaptada para o contexto da stack HortiReg.
  - `ata-review.txt`: Registro de demonstração e aceite com o PO.
  - `ata-retrospectiva.txt`: Pontos fortes, pontos a melhorar e plano de ação.
  - `metricas.txt`: Template de indicadores de esforço, velocidade e taxas de sucesso.

### 📁 Outras Pastas do Projeto (`arquitetura/`, `po/`, `qa/`, `releases/`)
- **`docs/arquitetura/descricao_projetoArquitetural.txt`**: Atualizado para a arquitetura real do HortiReg (FastAPI, React Vite, PostgreSQL, Evolution API WhatsApp, Google Gemini LLM).
- **`docs/po/definition-of-done.txt`**: Critérios em nível de história e release adaptados para a equipe.
- **`docs/po/priorizacao-do-backlog.txt`**: Histórias prioritárias alinhadas às releases do HortiReg.
- **`docs/po/release-notes/v0.1.0.txt`**: Notas da versão v0.1.0 (Release 1).
- **`docs/qa/README.md`**: Matriz de documentos de garantia da qualidade.
- **`docs/qa/Bugs_Sprint1_HortiReg.txt`**: Registro estruturado dos defeitos encontrados e corrigidos na R1.
- **`docs/qa/Casos_de_Teste_Sprint1_HortiReg.txt`**: Casos de teste funcionais e de aceitação para auth e catálogo.
- **`docs/releases/Relatorio_de_Qualidade_R1_HortiReg.txt`**: Relatório executivo de conformidade da Release 1.

---

## 2. O que Falta Modificar e Adicionar (Checklist de Pendências)

### 📌 1. Arquitetura (`docs/arquitetura/`)
- [ ] **Imagem do Diagrama Arquitetural:** Gerar e salvar a imagem `hortireg_projetoArquitetural.png` no diretório.
- [ ] **Refinamento de Integrações:** Descrever o tratamento de falhas em caso de indisponibilidade da API do Gemini ou da Evolution API.

### 📌 2. Product Owner (`docs/po/`)
- [ ] **Chaves do Jira:** Substituir chaves de exemplo (`HORTI-xx`) pelas chaves reais configuradas no Jira da equipe.
- [ ] **Link da Planilha de DoD:** Caso usem o Google Sheets para a Definition of Done, atualizar o link no arquivo `definition-of-done.txt`.
- [ ] **Backlog da Release 2:** Detalhar as histórias da R2 no Jira (webhooks WhatsApp e processamento de áudio).

### 📌 3. Qualidade (`docs/qa/`)
- [ ] **Planilhas e Documentos Vivos:** Adicionar/preencher os arquivos binários do pacote de qualidade:
  - `Plano_de_Qualidade v1.1.xlsx`
  - `Plano-de-Teste_v1.1.docx`
  - `GP_RiscoBaseadoDefeitos.xlsx`
- [ ] **Casos de Teste da Sprint 2:** Adicionar os cenários de teste para as novas features (processamento de áudio e pedidos).

### 📌 4. Scrum Master e Sprints (`docs/sm/`)
- [ ] **Arquivos Posteriores de Riscos e Impedimentos:** Criar `registro-de-impedimentos.txt` e `registro-de-riscos.txt` quando for definido o momento.
- [ ] **Gráfico Burndown da Sprint 1:** Exportar o gráfico do Jira e salvar como `docs/sm/sprints/sprint-1/burndown-sprint-1.png`.
- [ ] **Sprint 2:** Criar pasta `docs/sm/sprints/sprint-2/` e adicionar as atas de Planning, Review e Retrospectiva da Sprint 2 conforme ocorram.
- [ ] **Métricas Reais:** Preencher em `metricas.txt` a quantidade exata de PRs e execuções de CI registradas no GitHub Actions.
