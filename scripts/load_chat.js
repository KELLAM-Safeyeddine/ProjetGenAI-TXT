// Charge du protocole sur fixture exclusivement, jamais sur les données réelles.
import http from 'k6/http';
import { check,sleep } from 'k6';
export const options={vus:5,duration:'15s',noCookiesReset:true,thresholds:{http_req_failed:['rate<0.01'],http_req_duration:['p(95)<2000']}};
const base=__ENV.BASE_URL||'http://charge:5000';
let token='';
export default function(){
 if(!token){
  const login=http.get(base+'/login');
  const csrf=login.html().find('input[name="csrf_token"]').attr('value');
  http.post(base+'/login',{email:'charge@example.test',password:'Recette-charge-isolee-2026!',csrf_token:csrf});
  token=http.get(base+'/chat').html().find('meta[name="csrf-token"]').attr('content');
 }
 const response=http.post(base+'/api/chat',JSON.stringify({message:'Comment vérifier le niveau huile moteur ?',vehicle_id:1}),{headers:{'Content-Type':'application/json','X-CSRFToken':token}});
 check(response,{'réponse sourcée':r=>r.status===200&&r.json('source')==='manuel'&&r.json('references').length>0});
 sleep(0.2);
}
