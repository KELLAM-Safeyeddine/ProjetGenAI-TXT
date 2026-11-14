"""Commandes d’archives ; aucune n’est appelée par le chat ni le démarrage Docker."""

import click

from app import db
from app.models import VehicleCatalog
from app.services.chatbot_service import load_faq


def register_legacy(app):
    @app.cli.command('indexer-sources-web')
    def index_web():
        """Import limité aux URL vérifiées ; aucun téléchargement pendant le chat."""
        from pathlib import Path

        from app.models import WebPassage
        from app.services.web_sources import index_pages, load_sources, web_indexable

        try:
            sources = load_sources(app.config['WEB_SOURCES_PATH'])
        except (OSError, ValueError, KeyError, TypeError) as error:
            raise click.ClickException(
                'Liste de sources invalide ; index précédent conservé.'
            ) from error
        rows, journal = index_pages(sources)
        allowed = {s['url'] for s in sources if web_indexable(s)}
        # Les pages retirées de la liste ne peuvent plus être interrogées.
        db.session.execute(db.delete(WebPassage).where(WebPassage.url.not_in(allowed)))
        for url in {r['url'] for r in rows}:
            db.session.execute(db.delete(WebPassage).where(WebPassage.url == url))
        db.session.add_all([WebPassage(**row) for row in rows])
        db.session.commit()
        journal.append(
            f'{len({r["url"] for r in rows})}/{len(sources)} pages importées ; {len(rows)} passages. Les derniers passages autorisés sont conservés si une page devient inaccessible.'
        )
        click.echo('\n'.join(journal))
        path = Path(app.config['WEB_IMPORT_LOG'])
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text('\n'.join(journal) + '\n', encoding='utf-8')

    @app.cli.command('import-vehicules')
    def import_vehicles():
        """Synchronise les combinaisons documentées, sans modifier les véhicules privés."""
        from app.services.vehicle_catalog import UNKNOWN_ENGINE, load_catalog

        try:
            data = load_catalog()
        except (ValueError, KeyError, OSError) as error:
            raise click.ClickException(f'Catalogue invalide : {error}') from error
        # Validation complète avant toute mutation ; transaction atomique, import idempotent.
        db.session.execute(db.delete(VehicleCatalog))
        for row in data['vehicules']:
            db.session.add(
                VehicleCatalog(
                    brand=row['marque'],
                    model=row['modele'],
                    year=row['annee'],
                    engine_type=row['motorisation'] or UNKNOWN_ENGINE,
                    source=row['source'],
                    evidence={
                        k: v
                        for k, v in row.items()
                        if k not in ('marque', 'modele', 'annee', 'motorisation', 'source')
                    },
                )
            )
        db.session.commit()
        click.echo(
            f'{len(data["vehicules"])} combinaisons importées ({len({r["marque"] for r in data["vehicules"]})} marques).'
        )

    @app.cli.command('import-faq')
    @click.option(
        '--conserver-suppressions-anciennes',
        is_flag=True,
        help='Migration Docker : ne pas réintroduire une ancienne réponse supprimée.',
    )
    def import_faq(conserver_suppressions_anciennes):
        """Import idempotent ; actualise les réponses livrées intactes, préserve les éditions."""
        from app.services.faq_import import synchronize

        added, updated, preserved = synchronize(load_faq(), conserver_suppressions_anciennes)
        click.echo(
            f'{added} réponses importées ; {updated} actualisées ; {preserved} éditions/suppressions conservées.'
        )
