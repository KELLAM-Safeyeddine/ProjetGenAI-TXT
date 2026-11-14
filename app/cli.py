import click
from app import db
from app.models import User, FAQ, VehicleCatalog, ManuelPassage
from app.services.chatbot_service import load_faq

def register_cli(app):
    @app.cli.command('lister-vehicules-hors-liste')
    def list_outside_vehicles():
        """Liste les anciens véhicules hors périmètre sans modifier leurs données."""
        from app.models import Vehicle
        from app.services.manual_policy import reference_key
        from app.services.vehicle_catalog import allowed_vehicles
        allowed={reference_key(r['brand'],r['model'],r['year']) for r in allowed_vehicles()}
        count=0
        for vehicle in db.session.scalars(db.select(Vehicle).order_by(Vehicle.id)):
            if reference_key(vehicle.brand,vehicle.model,vehicle.year) not in allowed:
                click.echo(f'ID {vehicle.id} | compte {vehicle.user_id} | {vehicle.brand} | {vehicle.model} | {vehicle.year}')
                count+=1
        click.echo(f'{count} véhicule(s) hors liste. Aucune donnée modifiée.')

    @app.cli.command('lister-manuels-dacia')
    def list_dacia_manuals():
        """PDF trouvés, identités prouvées, indexation et motifs de rejet, sans écriture."""
        from app.services.manual_inventory import scan_manuals
        from app.services.manual_policy import reference_key
        try:inventory=scan_manuals(app.config['MANUALS_DIR'])
        except (ValueError,TypeError,OSError) as error:raise click.ClickException(f'Inventaire invalide : {error}') from error
        counts={reference_key(b,m,y):n for b,m,y,n in db.session.execute(db.select(ManuelPassage.brand,ManuelPassage.model,ManuelPassage.year,db.func.count(ManuelPassage.id)).where(ManuelPassage.active.is_(True)).group_by(ManuelPassage.brand,ManuelPassage.model,ManuelPassage.year))}
        for row in inventory:
            if row['statut']=='valide':
                ref=row['reference'];count=counts.get(reference_key(*ref.values()),0)
                click.echo(f"TROUVÉ Dacia {ref['modele']} {ref['annee']} | {row['chemin']} | "+(f'IMPORTÉ : {count} passages' if count else 'NON INDEXÉ : lancer flask import-manuels')+f" | {row['raison']}")
            else:click.echo(f"REJETÉ {row['chemin']} | {row['raison']}")
        click.echo(f"{len(inventory)} PDF trouvé(s), {sum(r['statut']=='valide' for r in inventory)} Dacia valide(s), {sum(r['statut']!='valide' for r in inventory)} rejeté(s).")

    @app.cli.command('indexer-sources-web')
    def index_web():
        """Import limité aux URL vérifiées ; aucun téléchargement pendant le chat."""
        from pathlib import Path
        from app.models import WebPassage
        from app.services.web_sources import load_sources,index_pages,web_indexable
        try:sources=load_sources(app.config['WEB_SOURCES_PATH'])
        except (OSError,ValueError,KeyError,TypeError) as error:
            raise click.ClickException('Liste de sources invalide ; index précédent conservé.') from error
        rows,journal=index_pages(sources)
        allowed={s['url'] for s in sources if web_indexable(s)}
        # Les pages retirées de la liste ne peuvent plus être interrogées.
        db.session.execute(db.delete(WebPassage).where(WebPassage.url.not_in(allowed)))
        for url in {r['url'] for r in rows}:
            db.session.execute(db.delete(WebPassage).where(WebPassage.url==url))
        db.session.add_all([WebPassage(**row) for row in rows]);db.session.commit()
        journal.append(f'{len({r["url"] for r in rows})}/{len(sources)} pages importées ; {len(rows)} passages. Les derniers passages autorisés sont conservés si une page devient inaccessible.')
        click.echo('\n'.join(journal))
        path=Path(app.config['WEB_IMPORT_LOG']);path.parent.mkdir(parents=True,exist_ok=True)
        path.write_text('\n'.join(journal)+'\n',encoding='utf-8')

    @app.cli.command('evaluer-chatbot')
    @click.option('--faq-fichier',is_flag=True,help='Option historique sans effet ; la FAQ générale locale est toujours utilisée sans véhicule.')
    @click.option('--cle-factice',type=click.Choice(['succes','erreur']),default=None)
    @click.option('--rapport',type=click.Path(path_type=__import__('pathlib').Path),default=None)
    def evaluate_chatbot(faq_fichier,cle_factice,rapport):
        """Vérifie les 78 questions inchangées avec un modèle simulant les outils."""
        from app.services.chatbot_evaluation import evaluate,write_report,ROOT
        transport=None
        if cle_factice=='erreur':
            from urllib.error import HTTPError
            def transport(*args):raise HTTPError('https://example.invalid',401,'simulated',{},None)
        results=evaluate(transport=transport)
        click.echo('FAQ générale locale sans véhicule ; modèle factice avec outils pour les manuels ; aucun appel réseau.')
        for row in results:
            click.echo(f"{row['case']['id']} {'OK' if row['correct'] else 'ÉCHEC'} -> {row['got']} ; appels={row['calls']}"+(' : '+' ; '.join(row['reasons']) if row['reasons'] else ''))
        passed,total=write_report(results,rapport or ROOT/'data/rapport_evaluation.md')
        click.echo(f'{passed}/{total} = {passed/total:.1%} ; rapport : {rapport or ROOT/"data/rapport_evaluation.md"}')
        if passed/total<.8:raise click.ClickException('Moins de 80 % de comportements conformes ; voir le rapport.')

    @app.cli.command('import-manuels')
    @click.option('--lecture-seule',is_flag=True,help='Indexe les PDF montés en lecture seule, sans réécrire leur manifeste.')
    def import_manuals(lecture_seule):
        """Synchronise le manifeste et les PDF locaux ; erreurs de PDF non fatales."""
        from app.services.manual_import import load_index, extract_manual
        from pathlib import Path
        from datetime import datetime, timezone
        root = Path(app.config['MANUALS_DIR'])
        try:
            entries, notices = load_index(root)
        except (ValueError, TypeError, KeyError, OSError) as error:
            raise click.ClickException(f'Manifeste invalide, index précédent conservé : {error}') from error
        lines = [f'Import {datetime.now(timezone.utc).isoformat()}', *notices]
        passages = []
        for entry in entries:
            label = f"{entry['marque']} {entry['modele']} {entry['annee']}"
            click.echo(f'Extraction : {label}…')
            try:
                extracted, warnings = extract_manual(entry)
                passages.extend(extracted)
                lines.append(f'{label} : {len(extracted)} passages.')
                lines.extend(f'AVERTISSEMENT {label} : {warning}' for warning in warnings)
            except Exception as error:
                # Un PDF corrompu, absent ou scanné ne bloque pas les autres manuels.
                lines.append(f'AVERTISSEMENT {label} : PDF absent ou illisible ({type(error).__name__}).')
        # Désactiver sans supprimer les anciennes versions, y compris PDF disparus.
        db.session.execute(db.update(ManuelPassage).values(active=False))
        existing={}
        for brand,model,year in {(p['brand'],p['model'],p['year']) for p in passages}:
            for row in db.session.scalars(db.select(ManuelPassage).where(ManuelPassage.brand==brand,ManuelPassage.model==model,ManuelPassage.year==year)):
                existing[(brand,model,year,row.page,row.position)]=row
        for values in passages:
            key=tuple(values[k] for k in ('brand','model','year','page','position'))
            row=existing.get(key)
            if row is None:db.session.add(ManuelPassage(**values,active=True))
            else:
                for name,value in values.items():setattr(row,name,value)
                row.active=True
        db.session.flush()
        from app.models import Vehicle
        from app.services.manual_access import references,link_manual
        known=references()
        for vehicle in db.session.scalars(db.select(Vehicle)):link_manual(vehicle,known)
        db.session.commit()
        indexed = {(p['brand'], p['model'], p['year']) for p in passages}
        catalog=[(e['marque'],e['modele'],e['annee']) for e in entries]
        lines.extend(f'SANS MANUEL : {brand} {model} {year}' for brand, model, year in catalog if (brand, model, year) not in indexed)
        lines.append(f'{len(indexed)} manuels indexés ; {len(passages)} passages ; {len(set(catalog) - indexed)} versions du catalogue sans manuel.')
        from app.services.manual_inventory import read_manifest
        import json
        document=read_manifest(root)
        imported={(e['chemin']):e for e in entries}
        kept=[]
        for old in document['manuels']:
            if old['chemin'] not in imported:kept.append({**old,'actif':False,'pret_import':False,'statut_import':'absent_ou_rejete'})
        for entry in entries:
            count=sum(p['brand']==entry['marque'] and p['model']==entry['modele'] and p['year']==entry['annee'] for p in passages)
            kept.append({**{k:v for k,v in entry.items() if k!='path'},'actif':bool(count),'statut_import':'importe' if count else 'sans_texte_indexable','passages_importes':count})
        document['manuels']=kept
        if not lecture_seule:
            temporary=root/'index.json.tmp'
            root.mkdir(parents=True,exist_ok=True)
            temporary.write_text(json.dumps(document,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
            temporary.replace(root/'index.json')
        else:
            lines.append('Montage en lecture seule : manifeste et PDF conservés ; état réel disponible avec flask list-manuels.')
        click.echo('\n'.join(lines))
        try:
            Path(app.config['MANUAL_IMPORT_LOG']).write_text('\n'.join(lines) + '\n', encoding='utf-8')
        except OSError:
            click.echo('Journal disponible dans cette sortie (écriture du fichier local impossible).')

    @app.cli.command('list-manuels')
    def list_manuals():
        """État réel de l'index en base, sans exposer de fichiers locaux."""
        rows = db.session.execute(db.select(ManuelPassage.brand, ManuelPassage.model, ManuelPassage.year,
            db.func.count(ManuelPassage.id)).where(ManuelPassage.active.is_(True)).group_by(ManuelPassage.brand, ManuelPassage.model, ManuelPassage.year)).all()
        for brand, model, year, count in rows:
            click.echo(f'{brand} {model} {year} : {count} passages')
        click.echo(f'{len(rows)} manuels indexés.')

    @app.cli.command('import-vehicules')
    def import_vehicles():
        """Synchronise les combinaisons documentées, sans modifier les véhicules privés."""
        from app.services.vehicle_catalog import load_catalog, UNKNOWN_ENGINE
        try:
            data = load_catalog()
        except (ValueError,KeyError,OSError) as error:
            raise click.ClickException(f'Catalogue invalide : {error}') from error
        # Validation complète avant toute mutation ; transaction atomique, import idempotent.
        db.session.execute(db.delete(VehicleCatalog))
        for row in data['vehicules']:
            db.session.add(VehicleCatalog(brand=row['marque'],model=row['modele'],year=row['annee'],
                engine_type=row['motorisation'] or UNKNOWN_ENGINE,source=row['source'],
                evidence={k:v for k,v in row.items() if k not in ('marque','modele','annee','motorisation','source')}))
        db.session.commit()
        click.echo(f"{len(data['vehicules'])} combinaisons importées ({len({r['marque'] for r in data['vehicules']})} marques).")

    @app.cli.command('import-faq')
    @click.option('--conserver-suppressions-anciennes',is_flag=True,help='Migration Docker : ne pas réintroduire une ancienne réponse supprimée.')
    def import_faq(conserver_suppressions_anciennes):
        """Import idempotent ; actualise les réponses livrées intactes, préserve les éditions."""
        from app.services.faq_import import synchronize
        added,updated,preserved=synchronize(load_faq(),conserver_suppressions_anciennes)
        click.echo(f'{added} réponses importées ; {updated} actualisées ; {preserved} éditions/suppressions conservées.')

    @app.cli.command('create-admin')
    @click.option('--name', prompt='Nom', default=None)
    @click.option('--email', prompt='Adresse email')
    @click.option('--password', prompt='Mot de passe (12 caractères minimum)', hide_input=True, confirmation_prompt=True)
    def create_admin(name, email, password):
        """Création explicite, aucun identifiant administrateur prédéfini."""
        import re
        email = email.strip().lower()
        if not name or not name.strip() or len(name) > 80 or len(email) > 254 or not re.fullmatch(r'[^\s@]+@[^\s@]+\.[^\s@]+', email):
            raise click.ClickException('Nom ou adresse email invalide.')
        if not 12 <= len(password) <= 128:
            raise click.ClickException('Le mot de passe doit contenir de 12 à 128 caractères.')
        if db.session.scalar(db.select(User).where(User.email == email)):
            raise click.ClickException('Cette adresse existe déjà. Aucun rôle n’a été modifié.')
        user = User(name=name.strip(), email=email, role='admin')
        user.set_password(password)
        db.session.add(user)
        db.session.commit()
        click.echo('Compte administrateur créé.')
