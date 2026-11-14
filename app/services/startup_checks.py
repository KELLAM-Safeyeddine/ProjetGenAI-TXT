"""Diagnostics de démarrage internes, sans afficher de secret ni appeler le modèle."""

from pathlib import Path

from app.services.llm_service import choose_provider


def report_startup(app):
    provider = choose_provider(app.config)
    if provider is None:
        app.logger.warning(
            'Assistant manuel : aucun fournisseur configuré. La FAQ générale sans véhicule reste disponible. Renseigner OPENAI_API_KEY ou GROQ_API_KEY dans la configuration privée pour le dialogue sur les manuels, puis redémarrer. Aucune clé n’est affichée aux utilisateurs.'
        )
    elif not provider.model or not provider.base_url:
        app.logger.warning(
            'Assistant manuel : configuration %s incomplète ; vérifier les variables *_MODEL et *_BASE_URL, puis redémarrer. La FAQ générale sans véhicule reste disponible.',
            provider.name,
        )
    else:
        app.logger.info(
            'Assistant : fournisseur %s configuré ; modèle et URL renseignés ; aucun appel réseau au démarrage.',
            provider.name,
        )
    root = Path(app.config['MANUALS_DIR'])
    if not root.is_dir():
        app.logger.warning(
            'Manuels : dossier MANUALS_DIR absent ; placer les PDF puis lancer flask import-manuels.'
        )
    elif not any(p.is_file() and p.suffix.lower() == '.pdf' for p in root.rglob('*')):
        app.logger.warning(
            'Manuels : aucun PDF local ; placer les PDF Dacia identifiables puis lancer flask import-manuels.'
        )
