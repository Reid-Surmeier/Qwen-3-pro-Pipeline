import { createRequire } from "node:module";
const require = createRequire("/home/reidsurmeier/.qwen-pipeline-claude-wt/godot/qa/web/node_modules/");
const { chromium } = require("playwright");
const OUT=process.argv[2];
const b=await chromium.launch(); const p=await b.newPage({viewport:{width:1536,height:1024},ignoreHTTPSErrors:true});
await p.goto("https://windows-wsl.taile06c45.ts.net/godot-v2-options/",{waitUntil:"networkidle",timeout:60000}); await p.waitForTimeout(8000);
const shot=async n=>p.screenshot({path:`${OUT}/${n}.png`,clip:{x:1090,y:280,width:446,height:290}});
await shot("00-idle");
// drag BGM thumb from ~1440 to 1236 with many moves, capture frames
await p.mouse.move(1440,355); await p.mouse.down(); const frames=[];
for(let i=1;i<=40;i++){ await p.mouse.move(1440-(204*i/40),355); await p.waitForTimeout(16); if(i%8==0) await shot(`01-drag-${i}`); }
await p.mouse.up(); await shot("01-drag-end");
// dropdown: open, hover row 3, commit
await p.mouse.click(1505,429); await p.waitForTimeout(300); await shot("02-dd-open");
await p.mouse.move(1300,442+26*3+6); await p.waitForTimeout(300); await shot("03-dd-hover-row3");
await p.mouse.click(1300,442+26*3+6); await p.waitForTimeout(300); await shot("04-dd-commit");
const st=await p.evaluate(()=>window.godotQaState); console.log(JSON.stringify({bgm:st.bgm,skin:st.skin,skin_open:st.skin_open,log:st.interaction_log?.length}));
await b.close();
