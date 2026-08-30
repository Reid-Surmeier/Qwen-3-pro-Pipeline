import { createRequire } from "node:module";
const require = createRequire("/home/reidsurmeier/.qwen-pipeline-claude-wt/godot/qa/web/node_modules/");
const { chromium } = require("playwright");
const OUT=process.argv[2];
const b=await chromium.launch(); const p=await b.newPage({viewport:{width:1536,height:1024},ignoreHTTPSErrors:true});
await p.goto("https://windows-wsl.taile06c45.ts.net/godot-v2-options-b/",{waitUntil:"networkidle",timeout:60000}); await p.waitForTimeout(9000);
const shot=async n=>p.screenshot({path:`${OUT}/${n}.png`,clip:{x:1090,y:280,width:446,height:300}});
const st=async()=>p.evaluate(()=>({bgm:window.godotQaState?.bgm,effect:window.godotQaState?.effect,skin:window.godotQaState?.skin,min:window.godotQaState?.minimized,open:window.godotQaState?.skin_open,hov:window.godotQaState?.hovered}));
await shot("00-idle");
// drag BGM thumb left with 40 moves; mid + end
await p.mouse.move(1440,355); await p.mouse.down();
for(let i=1;i<=40;i++){ await p.mouse.move(1440-(210*i/40),355); await p.waitForTimeout(14); if(i==20) await shot("01-drag-mid-held"); }
await p.mouse.up(); await shot("02-drag-left-clamped"); console.log("after left drag",JSON.stringify(await st()));
// right arrow x3
for(let i=0;i<3;i++){ await p.mouse.click(1472,355); await p.waitForTimeout(120);} await shot("03-arrow-right-x3");
// hover thumb
await p.mouse.move(1250,355); await p.waitForTimeout(500); await shot("04-hover-thumb");
// effect track click
await p.mouse.click(1300,389); await p.waitForTimeout(300); await shot("05-effect-track-click");
// checkbox toggle + hover
await p.mouse.click(1144,473); await p.waitForTimeout(250); await shot("06-attack-checked");
await p.mouse.click(1144,473); await p.waitForTimeout(250); await shot("07-attack-restored");
// dropdown open + hover row3 + commit
await p.mouse.click(1505,429); await p.waitForTimeout(400); await shot("08-dd-open");
await p.mouse.move(1300,429+13+19*2+10); await p.waitForTimeout(300); await shot("09-dd-hover");
await p.mouse.click(1300,429+13+19*2+10); await p.waitForTimeout(400); await shot("10-dd-commit"); console.log("after commit",JSON.stringify(await st()));
// minimize / restore
await p.mouse.click(1491,311); await p.waitForTimeout(300); await shot("11-minimized");
await p.mouse.click(1491,311); await p.waitForTimeout(300); await shot("12-restored");
// drag window + close + reopen
await p.mouse.move(1300,309); await p.mouse.down(); for(let i=1;i<=8;i++) await p.mouse.move(1300-50*i,309+30*i);
await p.mouse.up(); await p.screenshot({path:`${OUT}/13-window-dragged.png`});
await p.mouse.move(900,309+240); await p.mouse.down(); for(let i=8;i>=0;i--) await p.mouse.move(1300-50*i,309+30*i); await p.mouse.up();
await p.mouse.click(1517,312); await p.waitForTimeout(300); await p.screenshot({path:`${OUT}/14-closed.png`});
await p.mouse.click(35,20); await p.waitForTimeout(300); await shot("15-reopened"); console.log("final",JSON.stringify(await st()));
await b.close();
