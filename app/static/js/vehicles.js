(() => {
'use strict';
const form=document.getElementById('vehicle-form');if(!form)return;
const model=form.elements.model,year=form.elements.year;
const rows=JSON.parse(document.getElementById('allowed-vehicles').textContent);
const engine=form.elements.engine_version;
function updateEngines(){
 const old=engine.value;
 const values=rows.find(r=>r.model===model.value && String(r.year)===year.value)?.motorisations||[];
 engine.replaceChildren();
 for(const value of ['',...values]){const option=document.createElement('option');option.value=value;option.textContent=value||'Je ne sais pas';engine.append(option);}
 if(values.includes(old))engine.value=old;
}
function update(){
  const previous=year.value;
  const years=[...new Set(rows.filter(r=>r.model===model.value).map(r=>String(r.year)))];
  year.replaceChildren();
  if(!years.length){const option=document.createElement('option');option.value='';option.textContent='Choisir un modèle d’abord';year.append(option);}
  for(const value of years){const option=document.createElement('option');option.value=value;option.textContent=value;year.append(option);}
  if(years.includes(previous))year.value=previous;
  updateEngines();
}
model.addEventListener('change',update);
year.addEventListener('change',updateEngines);
// Conserver à l’ouverture la valeur historique ou la valeur du serveur après erreur.
if(!year.options.length)update();
})();
