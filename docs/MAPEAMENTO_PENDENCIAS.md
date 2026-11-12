# Mapeamento Consolidado de Estrutura e Pendências - HortiReg (SGV-WA)

Documento atualizado em **12/11/2026** refletindo as auditorias de qualidade, métricas reais das Sprints 1 e 2, catálogo de 22 User Stories e registro consolidado de impedimentos e riscos.

---

## 1. Status Geral das Pastas e Artefatos

### 📁 `docs/arquitetura/`
- [x] **`descricao_projetoArquitetural.txt`**: Documentado com a arquitetura completa da solução (FastAPI, React Vite, Evolution API, PostgreSQL 16, Gemini LLM).
- [x] **Diagrama Arquitetural (Mermaid)**: Inserido diretamente no arquivo de descrição e disponível para visualização gráfica, com detalhamento de todos os fluxos de mensagens, webhooks, autenticação e banco de dados.

### 📁 `docs/po/` (Product Owner)
- [x] **`priorizacao-do-backlog.txt`**: Atualizado com o catálogo completo de **22 User Stories (108 Story Points)** distribuídas em 4 Releases (R1: 21 SP, R2: 36 SP, R3: 34 SP, R4: 17 SP), incluindo os 9 Drivers Arquiteturais e as 9 tarefas de risco (TR-01 a TR-09).
- [x] **`definition-of-done.txt`**: Atualizado com os critérios acordados no nível de Sprint e Release, identificando responsáveis (QA verifica, PO aceita, SM mantém) e critérios técnicos específicos do projeto.
- [x] **`release-notes/v0.1.0.txt`**: Publicado com os marcos da Release 1.

### 📁 `docs/qa/` (Qualidade)
- [x] **`README.md`**: Matriz de documentos do plano de qualidade.
- [x] **`Bugs_Sprint1_HortiReg.txt`**: Auditoria corrigida (IMP-10 resolvido): registra que a R1 não possuía o tipo Bug no Jira e documenta os 5 bugs identificados na Sprint 2 (SCRUM-71 a SCRUM-75), com 4 corrigidos e apenas 1 médio aberto (BUG-03 mitigado na SCRUM-53).
- [x] **`Casos_de_Teste_Sprint1_HortiReg.txt`**: Matriz com os **61 casos de teste (CT-01 a CT-61)**, indicando quais já passam no CI (75 testes automatizados com 93,19% de cobertura) e guia passo a passo para implementar os pendentes.

### 📁 `docs/sm/` (Scrum Master)
- [x] **`acordos-de-trabalho.txt`**: Papéis definidos para R1 a R4 (PO e DevOps juntos da R2 em diante).
- [x] **`calendario-cerimonias.txt`**: Cronograma alinhado ao semestre acadêmico 2026.2.
- [x] **`registro-de-riscos.txt`**: Implementado com os **9 Riscos (RK-01 a RK-09)**, drivers associados, probabilidade, impacto, estratégias e tarefas no Jira (TR-01 a TR-09).
- [x] **`sprints/sprint-1/`**:
  * `ata-planning.txt`, `ata-review.txt`, `ata-retrospectiva.txt`, `metricas.txt`, `registro-dailies.txt`.
- [x] **`sprints/sprint-2/`**:
  * `ata-review.txt`: Registro da Review com itens demonstrados (US-06, US-08, US-10) e itens pendentes de Nidlan (US-07 não testada, US-09 não feita, DA-USAB-I3-03 não diretamente executado).
  * `ata-retrospectiva.txt`: Retrospectiva registrando pontos positivos (objetivos base e testes automatizados) e melhorias (gestão do tempo, comunicação, qualidade evitando acúmulo de PRs e documentação).
  * `metricas.txt`: Preenchido com dados medidos em 12/11/2026 (18 SP planejados, 16 entregues em CI, 5 pendentes na US-07).
  * `registro-de-impedimentos.txt`: Consolidado com os **11 impedimentos** (IMP-01 a IMP-11: 3 resolvidos, 3 parciais, 5 abertos).

---

## 2. Checklist do que Falta Fazer / Próximas Ações

1. **Jira e Governança:**
   - [ ] Registrar o aceite formal do PO (Julio) nas US-06, US-08, US-10 e RK-02 para permitir a transição para Done (IMP-09).
   - [ ] Cadastrar os bugs BUG-02, BUG-03, BUG-04 e BUG-05 como issues do tipo Bug no Jira (IMP-06).

2. **Ambiente e DevOps:**
   - [ ] Subir ambiente de homologação acessível para viabilizar testes reais de WhatsApp e deploy/rollback (IMP-07 / Q-09 / Q-10).
   - [ ] Ajustar as regras de proteção de branch para remover o bypass e exigir aprovação formal de PRs (IMP-05 / Q-04).

3. **Golden Set da IA:**
   - [ ] Gravar e disponibilizar o conjunto de 50 áudios com expressões regionais (SCRUM-47) para medir a precisão ≥ 90% da LLM (IMP-08 / Q-06 / DA-CONF-I1-01).

4. **Usabilidade:**
   - [ ] Agendar e executar a sessão de teste de usabilidade com 5 a 10 participantes (IMP-11 / Q-11 / DA-USAB-I1-03).
================================================================================
