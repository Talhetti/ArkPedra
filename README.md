# Prospecção inteligente de leads — Londrina/PR

Base pública de prospecção B2B com 100 empresas de Londrina, distribuídas em cinco nichos. O projeto gera um dashboard HTML estático, um JSON auditável e uma planilha Excel com acompanhamento comercial.

## Entregáveis

- `outputs/index.html`: dashboard responsivo e funcional sem backend.
- `outputs/leads_londrina.xlsx`: planilha com quatro abas, filtros, fórmulas, links, validação de status e formatação por prioridade.
- `outputs/leads_londrina.json`: base normalizada usada pelos dois entregáveis.

## Fontes e método

A coleta principal usa páginas públicas do Encontra Londrina. Para marmorarias, os dados de nota, avaliações, localização e coordenadas são complementados pelo Mármore Brasil. Algumas verificações específicas usam diretórios empresariais públicos, sempre com a URL registrada no próprio lead.

Regras aplicadas:

- nenhuma empresa é criada para completar a meta;
- cada nicho contém 20 empresas localizadas em Londrina;
- registros são deduplicados por nome, telefone e endereço normalizados;
- a falta de um resultado não vira automaticamente uma ausência confirmada;
- `NÃO` para site é usado somente após perfil sem domínio e busca exata complementar;
- indisponibilidade técnica de um site significa apenas falha de acesso na verificação, não lentidão ou defeito permanente;
- telefones móveis só são marcados como WhatsApp quando uma fonte pública declara esse canal.

## Atualizar a pesquisa

No ambiente Codex que contém o runtime de documentos:

```bash
python3 src/research.py --refresh --limit 20
python3 src/export_dashboard.py
node work/build_workbook.mjs
python3 src/finalize_excel_links.py
```

O coletor preserva as páginas consultadas em `data/raw/`. Para repetir a transformação sem nova consulta à internet, omita `--refresh`.

Após uma atualização, revise as entradas de `MANUAL_VERIFICATIONS` em `src/research.py`. Elas documentam verificações complementares que podem envelhecer. Confirme especialmente sites indisponíveis, números de WhatsApp e empresas marcadas como sem site.

## Dashboard

Abra `outputs/index.html` diretamente no navegador. Os dados estão incorporados no arquivo, portanto não há dependência de `fetch()` local. Status e observações comerciais são salvos no `localStorage` do navegador. A exportação para CSV/JSON inclui essas alterações, mas não modifica o Excel automaticamente.

## Limitações

- Google Maps apresentou uma visualização limitada no ambiente; os links abrem pesquisas por nome e endereço, e notas/avaliações só foram preenchidas quando outra fonte pública as publicou explicitamente.
- Instagram e Facebook podem limitar conteúdo sem autenticação. A existência do link foi registrada, mas e-commerce, catálogo e agendamento permanecem `NÃO IDENTIFICADO` quando não houve confirmação.
- Telefones e endereços de diretórios podem ficar desatualizados. Confirme antes da visita ou abordagem.
- O score é conservador: informação não verificada não recebe pontos de ausência.

