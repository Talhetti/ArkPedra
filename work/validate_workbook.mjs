import fs from "node:fs/promises";
import { FileBlob, SpreadsheetFile } from "@oai/artifact-tool";
const root=process.cwd(), path=`${root}/outputs/leads_londrina.xlsx`;
const wb=await SpreadsheetFile.importXlsx(await FileBlob.load(path));
wb.recalculate();
const inspections={
  summary:(await wb.inspect({kind:"table",range:"Resumo por Nicho!A2:H10",include:"values,formulas",tableMaxRows:10,tableMaxCols:8})).ndjson,
  pipeline:(await wb.inspect({kind:"table",range:"Prospecção Comercial!A2:J10",include:"values,formulas",tableMaxRows:10,tableMaxCols:10})).ndjson,
  errors:(await wb.inspect({kind:"match",searchTerm:"#REF!|#DIV/0!|#VALUE!|#NAME\\?|#N/A|#NUM!|#NULL!|#SPILL!|#CALC!",options:{useRegex:true,maxResults:300},summary:"final post-process formula error scan"})).ndjson
};
await fs.writeFile(`${root}/work/previews/final-inspection.json`,JSON.stringify(inspections,null,2));
for(const [sheetName,range,file] of [["Todos os Leads","A2:Q14","final-todos.png"],["Leads Prioritários","A2:O9","final-prioritarios.png"],["Resumo por Nicho","A2:H10","final-resumo.png"],["Prospecção Comercial","A2:J14","final-prospeccao.png"]]){const blob=await wb.render({sheetName,range,scale:1.2,format:"png"});await fs.writeFile(`${root}/work/previews/${file}`,new Uint8Array(await blob.arrayBuffer()));}
console.log(JSON.stringify(inspections,null,2));
