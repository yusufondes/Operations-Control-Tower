import fs from 'node:fs/promises';
import path from 'node:path';
import { pathToFileURL } from 'node:url';
import { Presentation, PresentationFile } from '@oai/artifact-tool';

const ROOT='C:/Users/yusuf/Operations-Control-Tower';
const SKILL='C:/Users/yusuf/.codex/plugins/cache/openai-primary-runtime/presentations/26.1013.11914/skills/presentations';
const WORK=process.env.HALY_DECK_WORKSPACE || 'C:/Users/yusuf/.codex/visualizations/2026/10/14/01a13cc0-b873-7160-ab31-6040221279c7/haly-deck';
const BUILD=path.join(WORK,'build');
const OUT=path.join(WORK,'output');
const {finalizePresentation,resolvePresentationFont}=await import(pathToFileURL(path.join(SKILL,'container_tools/artifact_tool_utils.mjs')).href);
const FONT=resolvePresentationFont({fontFamily:'Arial'});
const C={navy:'#102A3A',teal:'#096A6E',ink:'#183444',muted:'#526872',paper:'#F6F8F5',white:'#FFFFFF',rule:'#D6E1DE',soft:'#EEF3F1'};
const SLIDE_COUNT=14;
const TABLE_SLIDES=[4,12];
const p=Presentation.create({slideSize:{width:1280,height:720}});
const copies=[];
const noteSource='Repository: docs/DEMO.md; docs/TASKS.md, TASK-0007; docs/evidence/task-0007/README.md.';
const research='Presentation design reference: https://support.microsoft.com/en-us/powerpoint/tips-for-creating-and-delivering-an-effective-presentation and https://support.microsoft.com/en-us/powerpoint/combining-colors-in-powerpoint-mistakes-to-avoid';
function cleanCopy(value){return value.replace(/,([A-Za-z0-9])/g,', $1').replace(/([a-z])([0-9])/g,'$1 $2');}
function text(s,value,x,y,w,h,size=26,color=C.ink,bold=false,align='left'){
 const box=s.shapes.add({geometry:'textbox',name:'text-'+s.id+'-'+s.shapes.items.length,position:{left:x,top:y,width:w,height:h},fill:'none',line:{fill:'none',width:0}});
 box.text=cleanCopy(value); box.text.style={typeface:FONT,fontSize:size,bold,color,alignment:align,verticalAlignment:'top',autoFit:'none',wrap:'square',insets:0};
 return box;
}
function slide(title,summary='',dark=false){
 const s=p.slides.add(); s.background.fill=dark?C.navy:C.paper;
 const i=p.slides.items.length;
 if(title)text(s,title,64,52,1152,72,46,dark?C.white:C.navy,true);
 if(summary)text(s,summary,64,132,1152,54,26,dark?'#D4E6E2':C.muted);
 text(s,'HALY synthetic portfolio case study',64,677,1000,23,17,dark?'#BAD4D2':C.muted);
 text(s,String(i).padStart(2,'0')+' / '+SLIDE_COUNT,1110,677,106,23,17,dark?'#BAD4D2':C.muted,false,'right');
 return s;
}
function notes(s,body,sources=noteSource){s.speakerNotes.text=cleanCopy(body)+'\n\nSources: '+sources; copies.push({slide:p.slides.items.length,notes:cleanCopy(body),sources});}
async function image(s,file,x,y,w,h,crop,alt){
 const bytes=await fs.readFile(path.join(ROOT,file));
 s.images.add({blob:new Uint8Array(bytes),contentType:file.endsWith('.jpg')?'image/jpeg':'image/png',alt,fit:'contain',position:{left:x,top:y,width:w,height:h},...(crop?{crop}:{} )});
}
function crop(x,y,w,h){return{left:x/1280,top:y/720,right:(1280-x-w)/1280,bottom:(720-y-h)/720};}
async function shot(s,file,x,y,w,h,rect,alt){
 await image(s,'docs/evidence/task-0007/'+file,x,y,w,h,rect?crop(...rect):null,alt);
}
function table(s,values,x,y,w,h,widths){
 const t=s.tables.add({rows:values.length,columns:values[0].length,left:x,top:y,width:w,height:h,columnWidths:widths,values});
 t.styleOptions={headerRow:true,bandedRows:false};
 t.borders.assign({style:'solid',fill:C.rule,width:1});
 for(let r=0;r<values.length;r++){
  t.rows[r].height=h/values.length;
  for(let c=0;c<values[0].length;c++){
   const cell=t.getCell(r,c);cell.fill=r===0?C.navy:(r%2===1?C.white:C.soft);
   cell.text.style={typeface:FONT,fontSize:24,bold:r===0,color:r===0?C.white:C.ink,verticalAlignment:'middle',insets:10};
  }
 }
 return t;
}
function pair(s,number,title,body,y){
 text(s,number,64,y,70,64,42,C.teal,true);
 text(s,title,154,y+1,1040,38,28,C.navy,true);
 text(s,body,154,y+42,1040,47,24,C.muted);
}

// 01
{
 const s=slide('','',true);
 await image(s,'docs/portfolio/assets/haly-cover-concept.png',635,0,645,720,null,'AI-generated representative powdered-drink packaging and warehouse concept');
 text(s,'Operations\nControl Tower',64,168,550,190,70,C.white,true);
 text(s,'HALY seasonal campaign fulfilment\nBusiness case study',67,394,520,82,28,'#D4E6E2');
 text(s,'Yusuf Ondes',67,552,500,38,25,C.white,true);
 text(s,'Fictional company. Synthetic business data.',67,600,525,36,21,'#BAD4D2');
 // Cover keeps one footer instead of competing with the image.
 notes(s,'HALY is a fictional powdered-drink manufacturer. This portfolio demonstrates a realistic campaign-fulfilment problem with synthetic data. The project connects accepted dispatch promises to stock allocation, controlled shipments and accountable exceptions. It is a local demonstration with source published to a Private GitHub repository, not a production client implementation. The cover is an AI-generated representative concept image, not a photograph of an actual HALY company or facility.',noteSource+' '+research+' Cover asset: docs/portfolio/assets/haly-cover-concept.png. Generated with the built-in image tool on 15 October 2026.');
}
// 02
{
 const s=slide('The campaign stock gap','HALY makes powdered drinks using inputs from two suppliers.');
 text(s,'900',64,238,340,110,100,C.navy,true);
 text(s,'units ordered',68,360,335,42,29,C.ink);
 text(s,'500',466,238,340,110,100,C.teal,true);
 text(s,'finished units in stock',470,360,340,76,29,C.ink);
 text(s,'400',866,238,340,110,100,C.navy,true);
 text(s,'units to manufacture',870,360,340,76,29,C.ink);
 text(s,'The challenge: limited stock, competing dispatch dates.',64,530,1130,58,32,C.navy,true);
 text(s,'HALY produces the shortage in-house.',64,603,1130,38,27,C.muted);
 notes(s,'The synthetic campaign starts with 900 units of demand and 500 finished units on hand. HALY closes the remaining 400-unit gap through its own manufacturing process rather than buying finished products. Two suppliers provide raw materials. These values describe the validated end-to-end scenario, not a real sales forecast or measured company result.');
}
// 03
{
 const s=slide('Order fulfilment, step by step','Teams record physical work. Campaign rules control stock and shipment decisions.');
 pair(s,'01','Order and dispatch promise','Sales records the accepted warehouse dispatch date.',196);
 pair(s,'02','Stock allocation','Orders with earlier accepted dates receive available stock first.',286);
 pair(s,'03','Purchasing and production','HALY buys raw materials and manufactures the shortage.',376);
 pair(s,'04','Shipment','Individual orders ship in full. Corporate orders can ship in batches.',466);
 pair(s,'05','Exception follow-up','A linked risk item records the owner and next action.',556);
 notes(s,'This is the business workflow, not a claim that physical work happens automatically. Sales establishes the accepted warehouse dispatch commitment. The campaign addon allocates eligible stock under the approved policy. Procurement and manufacturing users record real input receipts and completed production. Warehouse users prepare and validate shipments. Derived risk information supports coordinated follow-up.');
}
// 04
{
 const s=slide('Dispatch dates set stock priority','Initial allocation of 500 finished units across three orders.');
 table(s,[['Order','Shipment policy','Ordered','Dispatch date','Allocated'],['A','Individual: complete','200','15 Dec 2026','200'],['B','Corporate: batches','600','16 Dec 2026','300'],['C','Individual: complete','100','17 Dec 2026','0'],['Total','','900','','500']],64,210,1152,335,[105,350,150,300,247]);
 text(s,'The accepted dispatch date sets priority for both customer types.',64,580,1150,66,30,C.teal,true);
 notes(s,'Initial allocation is A200, B300, C0. The first accepted dispatch date receives stock first. For equal dates, earlier confirmation wins. Stable order ID breaks an exact tie. An incomplete individual order retains its eligible allocated stock but cannot ship until complete. These are illustrative warehouse-dispatch dates, not delivery dates or a promised universal service level. Arithmetic: 200+600+100=900 ordered and 200+300+0=500 initially allocated.','docs/DEMO.md, Campaign walkthrough table; docs/DECISIONS.md,D-015; '+noteSource);
}
// 05
{
 const s=slide('A new date needs customer acceptance','Order B: 16 December originally, 14 December after recorded acceptance.');
 await shot(s,'04-accepted-date-history.png',64,208,1152,350,[20,250,1020,372],'Recorded synthetic order B showing original Dec16,current Dec14 and accepted response history');
 text(s,'Acceptance of a valid proposal updates the date.\nPending or rejected proposals keep the current date.',64,582,1152,76,27,C.teal,true);
 notes(s,'The real synthetic browser capture shows order B with original16 December and current14 December after a coordinator records acceptance. The original promise remains visible and response history identifies the applied change. A pending proposal, rejection, stale response or internal estimate does not move priority. Acceptance of the latest valid proposal updates the promise and can reprioritize stock not yet prepared. Staff record responses manually. The application does not authenticate customer consent or contact the customer. On rejection the existing promise and its risk remain visible, with an operational next action. The screenshot crop does not alter the source image.','docs/evidence/task-0007/04-accepted-date-history.png; docs/DECISIONS.md,D-011,D-012,D-015; '+noteSource);
}
// 06
{
 const s=slide('Stock follows the updated date',"B's accepted 14 December date comes before A's 15 December date.");
 await shot(s,'05-accepted-priority-reserves-500.png',64,208,1152,385,[25,165,1220,408],'Recorded synthetic B picking with demand600 and available quantity500 after accepted reprioritization');
 text(s,'B now has 500 units reserved. Prepared and non-campaign stock stays protected.',64,609,1152,54,27,C.teal,true);
 notes(s,'This is a later browser state, not the initial200/300/0 allocation. B has an accepted date of14 December and now receives all500 eligible unprepared units against600 demand. It wins because its promise is earlier, not because it is corporate. The application preserves prepared moves and outside reservations. It refuses unsupported or unmanaged competition rather than taking stock silently. A partly prepared short individual order needs warehouse unprepare/recheck before extra allocation.','docs/evidence/task-0007/05-accepted-priority-reserves-500.png; '+noteSource);
}
// 07
{
 const s=slide('Individual orders ship in full','Example: a user tries to ship 100 of the 200 units ordered.');
 await shot(s,'02-consumer-partial-blocked.png',64,215,1152,300,[60,255,1160,302],'Actual synthetic invalid-operation message refuses a100of200 individual partial shipment');
 text(s,'The partial shipment cannot be validated.',64,560,1140,60,32,C.teal,true);
 notes(s,'The browser screenshot shows an actual refused synthetic consumer shipment. Demand is200 and the entered quantity is100. Every physical line of the supported individual order must ship completely in one picking. Allocated stock can remain reserved while the order waits for completion. This is a policy-specific control within the configured one-step,untracked-goods scope.','docs/evidence/task-0007/02-consumer-partial-blocked.png; '+noteSource);
}
// 08
{
 const s=slide('Corporate orders can ship in batches','Browser example: 600 ordered, 300 shipped, 300 remaining.');
 text(s,'300 shipped',64,202,540,45,32,C.teal,true);
 text(s,'300 remaining',665,202,545,45,32,C.teal,true);
 await shot(s,'06-corporate-300-dispatched.png',64,260,550,285,[650,110,610,370],'Corporate picking shows Done and300 units shipped');
 await shot(s,'07-corporate-backorder-preserved.png',665,260,550,285,[650,110,610,420],'Corporate backorder shows300 demand and200 units currently reserved');
 text(s,'200 reserved for the next batch',665,550,550,34,24,C.muted);
 text(s,'The remaining 300 units stay on a backorder.',64,601,1130,50,30,C.navy,true);
 notes(s,'The left browser capture shows a300-unit corporate shipment completed. The right capture shows the retained300-unit backorder, with200 currently available/reserved. The remaining demand does not disappear when a batch leaves. This browser path later shipped100 and50 in separate checks; it is not the end-to-end300/200/100 manufacturing scenario shown later. No real shipment occurred.','docs/evidence/task-0007/06-corporate-300-dispatched.png; docs/evidence/task-0007/07-corporate-backorder-preserved.png; '+noteSource);
}
// 09
{
 const s=slide('HALY produces the missing 400 units','Two suppliers provide raw materials. HALY makes the finished product.');
 pair(s,'01','Purchase raw materials','Buy 400 units of each required input from two suppliers.',207);
 pair(s,'02','Receive the inputs','Record the materials arriving into stock.',311);
 pair(s,'03','Manufacture 400 finished units',"Complete HALY's own production order.",415);
 text(s,'500 opening + 400 manufactured = 900 units in total',64,560,1152,77,34,C.teal,true);
 notes(s,'This slide describes the validated automated purchase/manufacturing/dispatch scenario. Two400-unit raw-material POs supply two inputs. Their800 raw units are not800 finished units. The bill of materials and one400-unit manufacturing order produce400 finished goods,which combine with500 opening finished units. Procurement,receipt and production are recorded standard Odoo actions. The separate browser preview has no raw-material or manufacturing fixture.','scripts/validate_campaign.py; docs/evidence/task-0007/README.md; '+noteSource);
}
// 10
{
 const s=slide('Shortages have an owner','Each risk item links to its sales order and records the next action.');
 await shot(s,'03-owned-risk-item.png',64,210,1152,390,[25,125,1200,405],'Synthetic source-linked campaign risk item with owner,Blocked status,deadline and next action');
 text(s,"The coordinator can track the order's next action.",64,620,1150,40,27,C.teal,true);
 notes(s,'The browser capture shows a campaign shortage linked to the source order,with a coordinator,Blocked state and a next action. Separate runtime cases test supplier delay,one linked risk item and repeated updates without duplicates. Supply-risk dates use a one-level input/production signal,not exact order pegging or a guaranteed feasible date. A card/status does not imply physical shipment or customer contact.','docs/evidence/task-0007/03-owned-risk-item.png; '+noteSource);
}
// 11
{
 const s=slide('Preparation stays within allocated stock',"Warehouse users cannot prepare more than the order's allocation.");
 await shot(s,'12-final-preparation-guard.png',64,223,1152,270,[60,255,1160,272],'Final repaired synthetic browser guard refuses prepared quantity above allocated stock');
 text(s,'The system blocks the invalid quantity when the user saves.',64,552,1140,85,31,C.teal,true);
 notes(s,'This final-source browser capture demonstrates the repaired preparation guard. The application refuses a saved prepared quantity above the move allocation and asks the operator to reconcile availability. Independent review found two bypasses during development. Both were reproduced,repaired and retested. The final supported guards cover saved move/raw-line preparation and nested commands; they are not a claim that a privileged administrator cannot change any ERP data.','docs/evidence/task-0007/12-final-preparation-guard.png; docs/TASKS.md,TASK-0007 repair history.');
}
// 12
{
 const s=slide('All 900 units ship in the full test scenario','Automated local scenario, separate from the browser examples.');
 table(s,[['Order','Ordered','Shipment pattern','Total shipped'],['A: individual','200','In full','200'],['B: corporate','600','300 + 200 + 100','600'],['C: individual','100','In full','100'],['Total','900','','900']],64,212,1152,330,[310,180,430,232]);
 text(s,'500 opening + 400 manufactured = 900 dispatched',64,578,1152,52,33,C.teal,true);
 notes(s,'The actual local campaign probe passes the500+400=900 arithmetic. A ships200 completely,B ships600 in300/200/100 batches,C ships100 completely. Final main finished-goods stock is0. Seven final probe quants remain nonnegative and not over-reserved. These are synthetic test outcomes,not measured performance of a real operation. The browser screenshots depict a separate partial-shipment walkthrough.','scripts/validate_campaign.py; docs/evidence/task-0007/README.md.');
}
// 13
{
 const s=slide('What we built and checked','Standard Odoo operations with campaign-specific business rules.');
 text(s,'Standard operations',64,215,700,40,31,C.navy,true);
 text(s,'Sales, purchasing, inventory and own production.',64,258,710,58,26);
 text(s,'Added controls',64,337,700,40,31,C.navy,true);
 text(s,'Date history, stock priority and shipment safeguards.',64,380,710,62,26);
 text(s,'Review and testing',64,459,700,40,31,C.navy,true);
 text(s,'Independent review and regression checks.',64,502,710,64,26);
 text(s,'81',904,215,286,90,76,C.teal,true);
 text(s,'local test methods\npassed',904,306,290,70,24);
 text(s,'11',904,410,286,90,76,C.teal,true);
 text(s,'campaign cases\npassed',904,501,290,70,24);
 text(s,'Future options: capacity planning and carrier integration.',64,612,1152,38,24,C.muted);
 notes(s,'Yusuf owns the project and approved its business rules. The work includes requirement clarification, standard-flow assessment, focused extensions, synthetic scenarios, negative/concurrency checks and review-driven repairs. AI-assisted implementation supported this work. The recorded local result is81 methods:8 base,22 promise,51 campaign,plus11 campaign probe cases. These are historical local results, not81 GitHub CI tests and not business performance KPIs. No time-saving,ROI or delivery-rate improvement has been measured. Date history makes commitments visible, priority controls stock decisions, shipment guards enforce customer policy and a linked risk item assigns follow-up. Supported scope is one-step make-to-stock with configured untracked goods. Staff record customer responses and physical work. Capacity planning, carrier/WMS integration, formal quality release, authenticated consent and production hosting are not delivered. Future options are proposals, not approved commitments.','docs/TASKS.md,TASK-0003 through TASK-0008; docs/ARCHITECTURE.md; docs/DECISIONS.md; docs/evidence/task-0007/README.md.');
}
// 14
{
 const s=slide('Technology and source','Platform and tools used in the local demonstration.',true);
 text(s,'Business platform',64,216,460,40,29,'#9CD5CD',true);
 text(s,'Odoo 19 Community\nSales,Inventory,Purchase,Manufacturing',64,266,540,100,27,C.white);
 text(s,'Implementation',64,423,460,40,29,'#9CD5CD',true);
 text(s,'Python business rules\nXML views and CSV access controls',64,473,540,92,27,C.white);
 text(s,'Data and environment',700,216,500,40,29,'#9CD5CD',true);
 text(s,'PostgreSQL 15\nDocker and PowerShell validation helpers',700,266,510,100,27,C.white);
 text(s,'Version control',700,423,500,40,29,'#9CD5CD',true);
 const link=text(s,'Git and GitHub (private)',700,473,510,42,27,C.white);
 link.text.get('GitHub (private)').link={uri:'https://github.com/yusufondes/Operations-Control-Tower',isExternal:true};
 text(s,'Repository access required.',700,527,510,38,24,'#D4E6E2');
 text(s,'Synthetic demo. No production deployment. CI follow-up remains open.',64,609,1152,55,21,'#D4E6E2');
 notes(s,'Source repository: https://github.com/yusufondes/Operations-Control-Tower . The repository is Private at the verified publication checkpoint,so readers need access. No installation is needed to understand this deck. The source uses Odoo19 Community,Python,PostgreSQL15,Docker,XML/CSV and PowerShell. Git/GitHub retain both initial histories. Development was AI-assisted with Codex and independent agent review. Local81/11 checks passed. The first remote CI run passed repository checks and8 base tests but failed its later HTTP-health check with curl56; do not claim green CI or full campaign remote coverage. TASK-0008 preview-helper fixes are local/unpushed at this checkpoint. No production deployment or customer messaging exists.','README.md; compose.yaml; .github/workflows/ci.yml; docs/TASKS.md,TASK-0006,TASK-0008. Repository: https://github.com/yusufondes/Operations-Control-Tower . CI evidence: https://github.com/yusufondes/Operations-Control-Tower/actions/runs/38748554245 .');
}

if(p.slides.items.length!==SLIDE_COUNT) throw new Error('Unexpected slide count.');
await fs.mkdir(path.join(BUILD,'renders'),{recursive:true});
await fs.mkdir(OUT,{recursive:true});
await fs.writeFile(path.join(BUILD,'slide-copy.json'),JSON.stringify(copies,null,2));
for(const [i,s] of p.slides.items.entries()){
 const stem='slide-'+String(i+1).padStart(2,'0');
 const png=await p.export({slide:s,format:'png',scale:1.5});
 await fs.writeFile(path.join(BUILD,'renders',stem+'.png'),new Uint8Array(await png.arrayBuffer()));
 const layout=await s.export({format:'layout'});
 await fs.writeFile(path.join(BUILD,'renders',stem+'.json'),await layout.text());
 console.log('Rendered '+stem);
}
const draft=path.join(BUILD,'draft.pptx');
await(await PresentationFile.exportPptx(p)).save(draft);
const finalName=process.env.HALY_DECK_FILENAME || 'HALY-Operations-Control-Tower-Case-Study.pptx';
const result=await finalizePresentation({
 workspaceDir:WORK,candidatePath:draft,finalPath:path.join(OUT,finalName),explicitTotalSlideCount:SLIDE_COUNT,
 pythonExecutable:'C:/Users/yusuf/.cache/codex-runtimes/codex-primary-runtime/dependencies/python/python.exe',
 integrityValidatorPath:path.join(SKILL,'container_tools/inspect_presentation_package_integrity.py'),
 layoutValidatorPath:path.join(SKILL,'container_tools/inspect_presentation_layout_geometry.py'),
 layoutArgs:['--expected-slide-size-emu','12192000,6858000','--validate-bullet-geometry','--validate-heading-fit',...TABLE_SLIDES.flatMap(n=>['--require-native-table-slide',String(n)])],
 requiredNativeTableOwnerSlides:TABLE_SLIDES,fontPolicy:{basis:'design',families:[FONT]},
 verifyArtifactToolImport:true,receiptPath:path.join(BUILD,finalName+'.validation.json')
});
console.log(JSON.stringify(result));
