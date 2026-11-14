(() => {
'use strict';
const form=document.getElementById('vehicle-form');if(!form)return;
const model=form.elements.model,year=form.elements.year;
const rows=JSON.parse(document.getElementById('allowed-vehicles').textContent);
function update(){
  const previous=year.value;
  const years=[...new Set(rows.filter(r=>r.model===model.value).map(r=>String(r.year)))];
  year.replaceChildren();
  if(!years.length){const option=document.createElement('option');option.value='';option.textContent='Choisir un modèle d’abord';year.append(option);}
  for(const value of years){const option=document.createElement('option');option.value=value;option.textContent=value;year.append(option);}
  if(years.includes(previous))year.value=previous;
}
model.addEventListener('change',update);
// Conserver à l’ouverture la valeur historique ou la valeur du serveur après erreur.
if(!year.options.length)update();
})();
