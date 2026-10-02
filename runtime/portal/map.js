const protocol=new pmtiles.Protocol();maplibregl.addProtocol("pmtiles",protocol.tile);
const labelName=["coalesce",["get","name:es"],["get","name"],["get","name:latin"]];
const baseLayers=source=>[
{id:"background",type:"background",paint:{"background-color":"#0b100d"}},
{id:"landcover",type:"fill",source,"source-layer":"landcover",paint:{"fill-color":"#152319","fill-opacity":0.8}},
{id:"landuse",type:"fill",source,"source-layer":"landuse",paint:{"fill-color":"#162019","fill-opacity":0.55}},
{id:"water",type:"fill",source,"source-layer":"water",paint:{"fill-color":"#153149"}},
{id:"waterway",type:"line",source,"source-layer":"waterway",paint:{"line-color":"#356482","line-width":1}},
{id:"boundary",type:"line",source,"source-layer":"boundary",paint:{"line-color":"#66736a","line-dasharray":[3,2],"line-width":1}},
{id:"roads",type:"line",source,"source-layer":"transportation",paint:{"line-color":"#88968c","line-width":["interpolate",["linear"],["zoom"],5,0.4,14,2.4]}},
{id:"buildings",type:"fill",source,"source-layer":"building",minzoom:12,paint:{"fill-color":"#4b554f","fill-opacity":0.75}},
{id:"place-labels",type:"symbol",source,"source-layer":"place",layout:{"text-field":labelName,"text-size":["interpolate",["linear"],["zoom"],4,11,12,16],"text-allow-overlap":false,"text-padding":2},paint:{"text-color":"#e8eee9","text-halo-color":"#0b100d","text-halo-width":1.4}},
{id:"road-labels",type:"symbol",source,"source-layer":"transportation_name",minzoom:10,layout:{"symbol-placement":"line","text-field":labelName,"text-size":11,"text-rotation-alignment":"map","text-allow-overlap":false},paint:{"text-color":"#d0d8d2","text-halo-color":"#0b100d","text-halo-width":1.2}},
{id:"water-labels",type:"symbol",source,"source-layer":"water_name",minzoom:6,layout:{"text-field":labelName,"text-size":11},paint:{"text-color":"#8bc5e8","text-halo-color":"#0b100d","text-halo-width":1.2}}
];
function message(text){const el=document.querySelector("#mapMessage");el.hidden=!text;el.textContent=text||"";if(text)setTimeout(()=>{el.hidden=true},5000)}
function featureCenter(f){if(!f||!f.geometry)return null;const g=f.geometry;if(g.type==="Point")return g.coordinates;if(g.type==="LineString"&&g.coordinates.length)return g.coordinates[Math.floor(g.coordinates.length/2)];return null}
function installSearch(map){
 const input=document.querySelector("#mapSearch"),btn=document.querySelector("#mapSearchBtn");
 const go=()=>{
  const q=input.value.trim();if(!q)return;
  const m=q.match(/^\s*(-?\d+(?:\.\d+)?)\s*[, ]\s*(-?\d+(?:\.\d+)?)\s*$/);
  if(m){const lat=Number(m[1]),lon=Number(m[2]);if(Math.abs(lat)<=90&&Math.abs(lon)<=180){map.flyTo({center:[lon,lat],zoom:14});message("Coordenadas "+lat.toFixed(5)+", "+lon.toFixed(5));return}}
  const needle=q.toLocaleLowerCase("es");
  const feats=map.queryRenderedFeatures({layers:["place-labels","road-labels","water-labels"]});
  const found=feats.find(f=>Object.values(f.properties||{}).some(v=>typeof v==="string"&&v.toLocaleLowerCase("es").includes(needle)));
  const c=featureCenter(found);if(c){map.flyTo({center:c,zoom:Math.max(map.getZoom(),13)});message(found.properties?.["name:es"]||found.properties?.name||q)}
  else message("No está en las teselas visibles. Aleja/mueve el mapa o usa lat,lon.");
 };
 btn.addEventListener("click",go);input.addEventListener("keydown",e=>{if(e.key==="Enter"){e.preventDefault();go()}});
}
async function boot(){
 const maps=await fetch("/api/maps",{cache:"no-store"}).then(r=>r.json());const sel=document.querySelector("#mapSelect");
 if(!maps.length){sel.innerHTML="<option>Sin mapas</option>";return}
 const params=new URLSearchParams(location.search);let chosen=maps.find(x=>x.id===params.get("map"))||maps[0];
 for(const item of maps){const o=document.createElement("option");o.value=item.id;o.textContent=item.name;o.selected=item.id===chosen.id;sel.appendChild(o)}
 sel.addEventListener("change",()=>{const q=new URLSearchParams(location.search);q.set("map",sel.value);location.search=q.toString()});
 const sourceId="osm",source={type:"vector",url:"pmtiles://"+location.origin+chosen.url,attribution:"© OpenStreetMap contributors · OpenMapTiles"};
 const style={version:8,sources:{[sourceId]:source},layers:baseLayers(sourceId)};
 const map=new maplibregl.Map({container:"map",style,center:[-5.4,40.0],zoom:5.0,hash:true,maxZoom:15});
 map.addControl(new maplibregl.NavigationControl());map.addControl(new maplibregl.ScaleControl({unit:"metric"}));
 map.on("load",()=>installSearch(map));
}
boot().catch(e=>{document.querySelector("#mapSelect").innerHTML="<option>Mapa no disponible</option>";console.error(e);message("Mapa no disponible: "+e.message)});
