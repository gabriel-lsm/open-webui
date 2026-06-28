<RULE>
**Comportamento com Auto-Accept Ativado:**
Como o ambiente está configurado para "Auto-Accept" (execução automática de comandos e edições), siga rigorosamente estas duas exceções onde você DEVE parar e aguardar confirmação explícita do usuário:
1. **Planos de Implementação (`implementation_plan.md`):** Após criar ou modificar um plano de implementação, você deve obrigatoriamente aguardar a aprovação do usuário antes de iniciar a execução do código/comandos. Exija sempre a aprovação (`RequestFeedback: true` no metadata do artefato).
2. **Ambiguidade de Requisitos/Design:** Sempre que houver incerteza significativa sobre qual caminho arquitetural ou funcional seguir, não assuma um comportamento padrão. Interrompa a execução, apresente as opções de forma clara e aguarde a resposta do usuário antes de prosseguir.
</RULE>
