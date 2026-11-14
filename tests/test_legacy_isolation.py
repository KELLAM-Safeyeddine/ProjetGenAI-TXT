import gzip
import json

from app import db
from app.models import FAQ


def test_archive_export_is_explicit_and_never_deletes_or_overwrites(app, tmp_path):
    assert FAQ.__module__ == 'app.legacy.models'
    app.test_cli_runner().invoke(args=['import-faq'])
    path = tmp_path / 'archives.jsonl.gz'
    result = app.test_cli_runner().invoke(args=['exporter-archives', str(path)])
    assert result.exit_code == 0 and 'aucune suppression' in result.output
    with gzip.open(path, 'rt', encoding='utf8') as f:
        assert json.loads(next(f))['table'] == 'faq'
    assert app.test_cli_runner().invoke(args=['exporter-archives', str(path)]).exit_code == 1
    with app.app_context():
        assert db.session.scalar(db.select(db.func.count()).select_from(FAQ)) > 0
