import fs from 'node:fs/promises';
import path from 'node:path';
import { execFileSync } from 'node:child_process';
import { fileURLToPath } from 'node:url';
import { FileBlob, PresentationFile } from '@oai/artifact-tool';

const input=process.argv[2];
const output=process.argv[3];
const renderDir=process.argv[4];
if(!input || !output || !renderDir){
 throw new Error('Usage: node export_haly_pdf.mjs INPUT.pptx OUTPUT.pdf PRIVATE_RENDER_DIR');
}
try { await fs.access(output); throw new Error('Refusing to overwrite an existing PDF.'); }
catch(error){ if(error.code!=='ENOENT') throw error; }
const deck=await PresentationFile.importPptx(await FileBlob.load(input));
if(deck.slides.items.length!==14) throw new Error('Expected 14 slides.');
await fs.mkdir(renderDir,{recursive:true});
for(const [i,slide] of deck.slides.items.entries()){
 const png=await deck.export({slide,format:'png',scale:1.5});
 await fs.writeFile(path.join(renderDir,'slide-'+String(i+1).padStart(2,'0')+'.png'),new Uint8Array(await png.arrayBuffer()));
}
const python=process.env.HALY_PYTHON;
if(!python) throw new Error('Set HALY_PYTHON to a Python runtime with reportlab.');
execFileSync(python,[fileURLToPath(new URL('./export_haly_pdf.py',import.meta.url)),renderDir,output],{stdio:'inherit'});
console.log('Exported image-based PDF from the finalized 14-slide PowerPoint.');
