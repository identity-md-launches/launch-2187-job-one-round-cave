'use strict';
// One-shot finish: retain every ancestor pixel outside the new upper-rock mark.
const fs = require('node:fs');
const crypto = require('node:crypto');
const {decodePNG, encodePNG, preview} = require('./finish_wall.js');
const hash = b => crypto.createHash('sha256').update(b).digest('hex');
const old = fs.readFileSync('artifacts/line-1/wall.png');
const previous = JSON.parse(fs.readFileSync('dist/line-1/26.json','utf8'));
if(previous.image !== 'https://api.imd.fun/artifacts/'+hash(old)) throw Error('ancestor digest mismatch');
const ancestor=decodePNG('artifacts/line-1/wall.png');
const generated=decodePNG('artifacts/line-1/wall-v8.png');
if(ancestor.width!==generated.width || ancestor.height!==generated.height || ancestor.channels!==generated.channels) throw Error('dimensions differ');
const bounds=[796,600,958,736];
const out={...ancestor,pixels:Buffer.from(ancestor.pixels)};
let changed=0;
for(let y=bounds[1];y<bounds[3];y++) for(let x=bounds[0];x<bounds[2];x++) {
  const a=Math.min(1,(x-bounds[0])/7,(bounds[2]-1-x)/7,(y-bounds[1])/7,(bounds[3]-1-y)/7);
  const at=(y*out.width+x)*out.channels;
  for(let c=0;c<3;c++) out.pixels[at+c]=Math.round(ancestor.pixels[at+c]*(1-a)+generated.pixels[at+c]*a);
  if(!out.pixels.subarray(at,at+out.channels).equals(ancestor.pixels.subarray(at,at+ancestor.channels))) changed++;
}
let outside=true;
for(let y=0;y<out.height;y++) for(let x=0;x<out.width;x++) {
  if(x>=bounds[0] && x<bounds[2] && y>=bounds[1] && y<bounds[3]) continue;
  const at=(y*out.width+x)*out.channels;
  if(!out.pixels.subarray(at,at+out.channels).equals(ancestor.pixels.subarray(at,at+ancestor.channels))) outside=false;
}
if(!outside || changed<100) throw Error('preservation/mark check failed');
const png=encodePNG(out), jpeg=preview(out);
if(jpeg.length>100000) throw Error('JPEG exceeds 100 KB');
fs.writeFileSync('artifacts/line-1/wall-v8.png',png);
fs.writeFileSync('artifacts/line-1/wall.png',png);
fs.writeFileSync('dist/line-1/27.jpg',jpeg);
const report={bounds,changed_pixels:changed,all_pixels_outside_identical:outside,ancestor_sha256:hash(old),wall_sha256:hash(png),width:out.width,height:out.height,format:'PNG RGB8',png_bytes:png.length,preview:{width:512,height:512,format:'JPEG',bytes:jpeg.length}};
fs.writeFileSync('line-1/mark-process-27.json',JSON.stringify(report,null,2)+'\n');
console.log(JSON.stringify(report));
