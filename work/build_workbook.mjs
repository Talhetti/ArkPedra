import fs from "node:fs/promises";
import { SpreadsheetFile, Workbook } from "@oai/artifact-tool";

const root = process.cwd();
const data = JSON.parse(await fs.readFile(`${root}/data/leads_londrina.json`, "utf8"));
const outputDir = `${root}/outputs`;
const previewDir = `${root}/work/previews`;
await fs.mkdir(outputDir, { recursive: true });
await fs.mkdir(previewDir, { recursive: true });

const wb = Workbook.create();
const all = wb.worksheets.add("Todos os Leads");
const prioritySheet = wb.worksheets.add("Leads Prioritários");
const summary = wb.worksheets.add("Resumo por Nicho");
const pipeline = wb.worksheets.add("Prospecção Comercial");
const font = "Arial";
const colors = { navy: "#123B4A", teal: "#0E7C79", pale: "#EAF3F3", line: "#D7E2E5", ink: "#17252D", muted: "#667782", amber: "#F4B942", red: "#C8553D", blue: "#3E6FA8" };
const headers = [
  "ID","Empresa","Nicho","Endereço","Bairro","Cidade","UF","Telefone","WhatsApp confirmado","WhatsApp",
  "Google Maps","Nota Google","Avaliações","Site","Situação do site","Verificação técnica do site","HTTP","Presença digital",
  "Instagram","Facebook","E-commerce","Catálogo digital","Agendamento online","Principais serviços","Oportunidades identificadas",
  "Soluções recomendadas","Abordagem sugerida","Fatos observados","Score","Prioridade","Justificativa do score",
  "Fonte 1","Fonte 2","Fonte 3","Data de verificação","Status comercial","Observações comerciais","Latitude","Longitude"
];

const urlFormula = (url, label) => url ? `=HYPERLINK("${String(url).replaceAll('"','""')}","${label}")` : "";
const leadRows = data.map(l => [
  l.id,l.name,l.niche,l.address,l.bairro,l.city,l.state,l.phone,l.whatsapp_status,l.whatsapp,
  null,l.rating,l.review_count,null,l.site_status,l.site_check_result,l.site_http_status,l.presence_status,
  null,null,l.ecommerce_status,l.catalog_status,l.appointment_status,l.services,l.opportunities,l.recommended_solutions,
  l.suggested_approach,l.observed_facts,l.score,l.priority,l.score_justification,
  null,null,null,new Date(`${l.verified_at}T12:00:00`),l.commercial_status,l.commercial_notes,l.latitude ?? null,l.longitude ?? null
]);

function baseSheet(sheet, title, subtitle) {
  sheet.showGridLines = false;
  sheet.getRange("A2").values = [[title]];
  sheet.getRange("A2").format.font = { name: font, size: 15, bold: true, color: colors.navy };
  sheet.getRange("A3").values = [[subtitle]];
  sheet.getRange("A3").format.font = { name: font, size: 10, italic: true, color: colors.muted };
  sheet.getRange("A2:AM3").format.verticalAlignment = "center";
}

function headerStyle(range) {
  range.format.fill = colors.navy;
  range.format.font = { name: font, size: 10, bold: true, color: "#FFFFFF" };
  range.format.horizontalAlignment = "center";
  range.format.verticalAlignment = "center";
  range.format.wrapText = true;
  range.format.rowHeight = 34;
  range.format.borders = { preset: "inside", style: "thin", color: "#FFFFFF" };
}

function applyCommonLeadFormatting(sheet, lastRow, lastCol="AM") {
  sheet.getRange(`A2:${lastCol}${lastRow}`).format.font = { name: font, size: 10, color: colors.ink };
  headerStyle(sheet.getRange(`A4:${lastCol}4`));
  sheet.getRange(`A5:${lastCol}${lastRow}`).format.verticalAlignment = "top";
  sheet.getRange(`A5:${lastCol}${lastRow}`).format.borders = { insideHorizontal: { style: "thin", color: "#E8EEF0" } };
  sheet.getRange(`D5:E${lastRow}`).format.wrapText = true;
  sheet.getRange(`X5:AE${lastRow}`).format.wrapText = true;
  sheet.getRange(`AF5:AH${lastRow}`).format.wrapText = true;
  sheet.getRange(`L5:L${lastRow}`).format.numberFormat = "0.0";
  sheet.getRange(`M5:M${lastRow}`).format.numberFormat = "#,##0";
  sheet.getRange(`Q5:Q${lastRow}`).format.numberFormat = "0";
  sheet.getRange(`AC5:AC${lastRow}`).format.numberFormat = "0";
  sheet.getRange(`AI5:AI${lastRow}`).format.numberFormat = "dd/mm/yyyy";
  sheet.getRange(`AL5:AM${lastRow}`).format.numberFormat = "0.00000";
  sheet.getRange(`AC5:AC${lastRow}`).conditionalFormats.add("colorScale", { colors: ["#E8EEF0", "#FDE7A9", "#D66A50"], thresholds: ["min", {type:"percentile", value:50}, "max"] });
  const pr = sheet.getRange(`AD5:AD${lastRow}`);
  pr.conditionalFormats.add("containsText", { text: "Prioridade A", format: { fill: "#FDE2DD", font: { color: "#8C2F20", bold: true } } });
  pr.conditionalFormats.add("containsText", { text: "Prioridade B", format: { fill: "#FFF0C9", font: { color: "#7B5700", bold: true } } });
  pr.conditionalFormats.add("containsText", { text: "Prioridade C", format: { fill: "#DFEAF7", font: { color: "#2D5680", bold: true } } });
  pr.conditionalFormats.add("containsText", { text: "Prioridade D", format: { fill: "#E8EDEF", font: { color: "#53646C", bold: true } } });
  sheet.freezePanes.freezeRows(4);
  sheet.freezePanes.freezeColumns(2);
  const widths = {
    A:14,B:30,C:28,D:42,E:24,F:14,G:7,H:17,I:18,J:17,K:14,L:12,M:12,N:14,O:18,P:24,Q:10,R:22,S:14,T:14,U:16,V:18,W:20,
    X:46,Y:54,Z:50,AA:52,AB:44,AC:10,AD:25,AE:56,AF:30,AG:30,AH:30,AI:16,AJ:18,AK:30,AL:13,AM:13
  };
  for (const [col,width] of Object.entries(widths)) sheet.getRange(`${col}:${col}`).format.columnWidth = width;
}

baseSheet(all, "Prospecção inteligente de leads — Londrina/PR", "100 empresas públicas, 20 por nicho. Informações não confirmadas permanecem como não identificadas.");
all.getRange("A4:AM4").values = [headers];
all.getRange(`A5:AM${4+leadRows.length}`).values = leadRows;
const allLast = 4 + leadRows.length;
all.getRange(`K5:K${allLast}`).formulas = data.map(l => [urlFormula(l.maps_url,"Abrir mapa")]);
all.getRange(`N5:N${allLast}`).formulas = data.map(l => [urlFormula(l.website,"Abrir site")]);
all.getRange(`S5:S${allLast}`).formulas = data.map(l => [urlFormula(l.instagram,"Instagram")]);
all.getRange(`T5:T${allLast}`).formulas = data.map(l => [urlFormula(l.facebook,"Facebook")]);
all.getRange(`AF5:AF${allLast}`).formulas = data.map(l => [urlFormula(l.sources?.[0],"Fonte 1")]);
all.getRange(`AG5:AG${allLast}`).formulas = data.map(l => [urlFormula(l.sources?.[1],"Fonte 2")]);
all.getRange(`AH5:AH${allLast}`).formulas = data.map(l => [urlFormula(l.sources?.[2],"Fonte 3")]);
applyCommonLeadFormatting(all, allLast);
all.tables.add(`A4:AM${allLast}`, true, "TodosLeadsTable").style = "TableStyleMedium2";
all.tabColor = colors.navy;

const prioritized = data.filter(l => l.score >= 60).sort((a,b)=>b.score-a.score || a.name.localeCompare(b.name));
const pHeaders = ["Empresa","Nicho","Bairro","Telefone","WhatsApp","Site","Instagram","Score","Prioridade","Oportunidade principal","Soluções recomendadas","Abordagem sugerida","Google Maps","Data de verificação","Fonte principal"];
baseSheet(prioritySheet, "Leads prioritários", "Empresas com score igual ou superior a 60, ordenadas por pontuação.");
prioritySheet.getRange("A4:O4").values = [pHeaders];
prioritySheet.getRange(`A5:O${4+prioritized.length}`).values = prioritized.map(l=>[l.name,l.niche,l.bairro,l.phone,l.whatsapp||l.whatsapp_status,null,null,l.score,l.priority,l.opportunities,l.recommended_solutions,l.suggested_approach,null,new Date(`${l.verified_at}T12:00:00`),null]);
const pLast=4+prioritized.length;
prioritySheet.getRange(`F5:F${pLast}`).formulas = prioritized.map(l=>[urlFormula(l.website,"Abrir site")]);
prioritySheet.getRange(`G5:G${pLast}`).formulas = prioritized.map(l=>[urlFormula(l.instagram,"Instagram")]);
prioritySheet.getRange(`M5:M${pLast}`).formulas = prioritized.map(l=>[urlFormula(l.maps_url,"Abrir mapa")]);
prioritySheet.getRange(`O5:O${pLast}`).formulas = prioritized.map(l=>[urlFormula(l.sources?.[0],"Fonte")]);
prioritySheet.showGridLines=false;prioritySheet.getRange(`A2:O${pLast}`).format.font={name:font,size:10,color:colors.ink};headerStyle(prioritySheet.getRange("A4:O4"));
prioritySheet.getRange(`A5:O${pLast}`).format.verticalAlignment="top";prioritySheet.getRange(`J5:L${pLast}`).format.wrapText=true;prioritySheet.getRange(`H5:H${pLast}`).format.numberFormat="0";prioritySheet.getRange(`N5:N${pLast}`).format.numberFormat="dd/mm/yyyy";
prioritySheet.getRange(`I5:I${pLast}`).conditionalFormats.add("containsText",{text:"Prioridade B",format:{fill:"#FFF0C9",font:{color:"#7B5700",bold:true}}});
for(const [c,w] of Object.entries({A:34,B:27,C:24,D:17,E:18,F:14,G:14,H:10,I:24,J:56,K:50,L:55,M:14,N:16,O:14}))prioritySheet.getRange(`${c}:${c}`).format.columnWidth=w;
prioritySheet.freezePanes.freezeRows(4);prioritySheet.freezePanes.freezeColumns(1);prioritySheet.tables.add(`A4:O${pLast}`,true,"PriorityLeadsTable").style="TableStyleMedium2";prioritySheet.tabColor=colors.teal;

const niches=[...new Set(data.map(l=>l.niche))];
const opportunityByNiche={
  "Marmorarias":"Site/portfólio e orçamento visual",
  "Vidraçarias":"Catálogo de projetos e solicitação de orçamento",
  "Marcenarias e móveis planejados":"Portfólio de ambientes e qualificação de orçamento",
  "Oficinas mecânicas":"Agendamento, pré-triagem e lembretes",
  "Serralherias":"Portfólio por tipo de estrutura e orçamento"
};
summary.showGridLines=false;summary.getRange("A2").values=[["Resumo por nicho"]];summary.getRange("A2").format.font={name:font,size:15,bold:true,color:colors.navy};summary.getRange("A3").values=[["Indicadores calculados a partir da aba Todos os Leads."]];summary.getRange("A3").format.font={name:font,size:10,italic:true,color:colors.muted};
summary.getRange("A4:H4").values=[["Nicho","Empresas","Leads prioritários","Site confirmado","Sem site confirmado","Site não identificado","Score médio","Principais oportunidades"]];headerStyle(summary.getRange("A4:H4"));
summary.getRange(`A5:A${4+niches.length}`).values=niches.map(n=>[n]);summary.getRange(`H5:H${4+niches.length}`).values=niches.map(n=>[opportunityByNiche[n]]);
for(let i=0;i<niches.length;i++){const r=5+i;summary.getRange(`B${r}`).formulas=[[`=COUNTIF('Todos os Leads'!$C$5:$C$${allLast},A${r})`]];summary.getRange(`C${r}`).formulas=[[`=COUNTIFS('Todos os Leads'!$C$5:$C$${allLast},A${r},'Todos os Leads'!$AC$5:$AC$${allLast},">=60")`]];summary.getRange(`D${r}`).formulas=[[`=COUNTIFS('Todos os Leads'!$C$5:$C$${allLast},A${r},'Todos os Leads'!$O$5:$O$${allLast},"SIM")`]];summary.getRange(`E${r}`).formulas=[[`=COUNTIFS('Todos os Leads'!$C$5:$C$${allLast},A${r},'Todos os Leads'!$O$5:$O$${allLast},"NÃO")`]];summary.getRange(`F${r}`).formulas=[[`=COUNTIFS('Todos os Leads'!$C$5:$C$${allLast},A${r},'Todos os Leads'!$O$5:$O$${allLast},"NÃO IDENTIFICADO")`]];summary.getRange(`G${r}`).formulas=[[`=AVERAGEIF('Todos os Leads'!$C$5:$C$${allLast},A${r},'Todos os Leads'!$AC$5:$AC$${allLast})`]];}
summary.getRange(`A5:H${4+niches.length}`).format.font={name:font,size:10,color:colors.ink};summary.getRange(`A5:H${4+niches.length}`).format.verticalAlignment="top";summary.getRange(`H5:H${4+niches.length}`).format.wrapText=true;summary.getRange(`B5:F${4+niches.length}`).format.numberFormat="0";summary.getRange(`G5:G${4+niches.length}`).format.numberFormat="0.0";summary.getRange(`A4:H${4+niches.length}`).format.borders={insideHorizontal:{style:"thin",color:"#E8EEF0"}};
for(const [c,w] of Object.entries({A:32,B:14,C:19,D:17,E:19,F:22,G:14,H:52}))summary.getRange(`${c}:${c}`).format.columnWidth=w;summary.tabColor=colors.navy;

const pipeHeaders=["Empresa","Nicho","Score","Prioridade","Responsável pela abordagem","Status","Data do contato","Próxima ação","Valor proposto","Observações"];
pipeline.showGridLines=false;pipeline.getRange("A2").values=[["Prospecção comercial"]];pipeline.getRange("A2").format.font={name:font,size:15,bold:true,color:colors.navy};pipeline.getRange("A3").values=[["Preencha os campos em amarelo. Esta aba é um acompanhamento manual e não é atualizada pelo dashboard HTML."]];pipeline.getRange("A3").format.font={name:font,size:10,italic:true,color:colors.muted};pipeline.getRange("A4:J4").values=[pipeHeaders];headerStyle(pipeline.getRange("A4:J4"));
pipeline.getRange(`A5:D${allLast}`).formulas=data.map((_,i)=>{const sourceRow=5+i;return [[`='Todos os Leads'!B${sourceRow}`,`='Todos os Leads'!C${sourceRow}`,`='Todos os Leads'!AC${sourceRow}`,`='Todos os Leads'!AD${sourceRow}`]]}).flat();
pipeline.getRange(`E5:J${allLast}`).values=data.map(l=>["",l.commercial_status,"", "", null, ""]);
pipeline.getRange(`E5:J${allLast}`).format.fill="#FFF8DD";pipeline.getRange(`A5:J${allLast}`).format.font={name:font,size:10,color:colors.ink};pipeline.getRange(`A5:J${allLast}`).format.verticalAlignment="top";pipeline.getRange(`J5:J${allLast}`).format.wrapText=true;pipeline.getRange(`G5:G${allLast}`).format.numberFormat="dd/mm/yyyy";pipeline.getRange(`I5:I${allLast}`).format.numberFormat='"R$" #,##0.00';pipeline.getRange(`C5:C${allLast}`).format.numberFormat="0";
pipeline.getRange(`F5:F${allLast}`).dataValidation={rule:{type:"list",values:["não contatado","contatado","interessado","reunião","proposta enviada","fechado","perdido"]}};
const statusRange=pipeline.getRange(`F5:F${allLast}`);statusRange.conditionalFormats.add("containsText",{text:"interessado",format:{fill:"#DFF3EF",font:{color:"#075F5C",bold:true}}});statusRange.conditionalFormats.add("containsText",{text:"fechado",format:{fill:"#CDEBDD",font:{color:"#175C3A",bold:true}}});statusRange.conditionalFormats.add("containsText",{text:"perdido",format:{fill:"#FDE2DD",font:{color:"#8C2F20",bold:true}}});
for(const [c,w] of Object.entries({A:34,B:28,C:10,D:24,E:25,F:20,G:16,H:34,I:18,J:45}))pipeline.getRange(`${c}:${c}`).format.columnWidth=w;pipeline.freezePanes.freezeRows(4);pipeline.freezePanes.freezeColumns(1);pipeline.tables.add(`A4:J${allLast}`,true,"CommercialPipelineTable").style="TableStyleMedium2";pipeline.tabColor=colors.teal;

wb.recalculate();
const checks={};
checks.all=(await wb.inspect({kind:"table",range:"Todos os Leads!A2:Q12",include:"values,formulas",tableMaxRows:12,tableMaxCols:17})).ndjson;
checks.summary=(await wb.inspect({kind:"table",range:"Resumo por Nicho!A2:H10",include:"values,formulas",tableMaxRows:10,tableMaxCols:8})).ndjson;
checks.pipeline=(await wb.inspect({kind:"table",range:"Prospecção Comercial!A2:J10",include:"values,formulas",tableMaxRows:10,tableMaxCols:10})).ndjson;
checks.errors=(await wb.inspect({kind:"match",searchTerm:"#REF!|#DIV/0!|#VALUE!|#NAME\\?|#N/A|#NUM!|#NULL!|#SPILL!|#CALC!",options:{useRegex:true,maxResults:300},summary:"final formula error scan"})).ndjson;
await fs.writeFile(`${previewDir}/inspection.json`,JSON.stringify(checks,null,2));
for(const [sheetName,range,file] of [["Todos os Leads","A2:Q14","todos.png"],["Leads Prioritários",`A2:O${Math.min(pLast,10)}`,"prioritarios.png"],["Resumo por Nicho","A2:H10","resumo.png"],["Prospecção Comercial","A2:J14","prospeccao.png"]]){const blob=await wb.render({sheetName,range,scale:1.2,format:"png"});await fs.writeFile(`${previewDir}/${file}`,new Uint8Array(await blob.arrayBuffer()));}
const out=await SpreadsheetFile.exportXlsx(wb);await out.save(`${outputDir}/leads_londrina.xlsx`);
console.log(JSON.stringify({rows:data.length,prioritized:prioritized.length,output:`${outputDir}/leads_londrina.xlsx`,previews:previewDir},null,2));
