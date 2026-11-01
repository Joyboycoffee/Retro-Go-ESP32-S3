// Emulate MicroQuickJS limits + mock Bruce modules
for (const m of ["startsWith","endsWith","includes","padStart","padEnd","repeat"]) delete String.prototype[m];
delete globalThis.encodeURIComponent; delete globalThis.encodeURI;
const fs = require("fs");
const file = process.argv[2], scenario = process.argv[3];
let t = 0, draws = [], pins = {40:1,41:1,42:1,45:1,48:1}, calls = {};
let sel = false, esc = false, unlockedPad = 0, escQueue = [];
const display = { color:(r,g,b)=>r<<16|g<<8|b, width:()=>320, height:()=>240, fill(){}, drawFillRect(){}, drawLine(){},
  setTextAlign(){}, setTextSize(){}, setTextColor(){}, drawText(s){ draws.push(String(s)); }, drawRect(){}, drawRoundRect(){}, drawFillRoundRect(){}, drawCircle(){}, drawFillCircle(){}, drawPixel(){}, setFont(){}, drawString(){} };
const keyboard = { getEscPress:()=>{ return escQueue.length? escQueue.shift():false; }, getSelPress:()=>{ calls.sel=(calls.sel||0)+1; return scenario==="A-pressed" && calls.sel<3; },
  getPrevPress:()=>false, getNextPress:()=>false, getAnyPress:()=>false,
  numKeyboard:()=>{ unlockedPad++; return "0000"; }, keyboard:()=>"hello world" };
const gpio = { pinMode(){}, digitalRead:(p)=>pins[p] };
const device = { getBatteryCharge:()=>scenario==="nobat"?-1:93, getBatteryDetailed:()=>({battery_percent:93}) };
const wifi = { connected:()=>true, httpFetch:(u)=>{ calls.url=u; return {ok:true,status:200,body:'{"title":"Hello","extract":"Hello is a greeting “quoted”."}'}; } };
const storage={read:()=>JSON.stringify({password:"4321"}),write(){}}; const mods={display,keyboard,gpio,device,wifi,storage,audio:{},dialog:{}};
globalThis.require = n => mods[n] || {};
globalThis.delay = ms => { t += ms; pins = Object.assign({40:1,41:1,42:1,45:1,48:1}, scenarioPins(t)); if (t > 4000) { escQueue.push(true); } if (t>6000) throw new Error("__done__"); };
globalThis.now = () => t; 
const RealDate = Date;
function scenarioPins(t){
  if (scenario==="select" && t>500 && t<800) return {40:0};
  if (scenario==="xmode" && t>200 && t<400) return {45:0};
  return {};
}
let src = fs.readFileSync(file,"utf8");
try { new Function(src)(); } catch(e){ if(e.message!=="__done__") { console.log("THROW:", e.message); process.exit(1);} }
console.log(JSON.stringify({scenario, padOpened:unlockedPad, draws:draws.length, sampleBattery:draws.filter(s=>/%/.test(s)).slice(0,3), url:calls.url||null}));
