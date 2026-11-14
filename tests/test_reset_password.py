from app import db
from app.models import User


def test_operator_reset_invalidates_open_sessions_and_does_not_disclose_existence(app, alice):
    runner = app.test_cli_runner()
    password = 'Mot-de-passe-nouveau-2026!'
    known = runner.invoke(
        args=['reset-password', 'alice@example.test'], input=password + '\n' + password + '\n'
    )
    unknown = runner.invoke(
        args=['reset-password', 'absent@example.test'], input=password + '\n' + password + '\n'
    )
    assert known.exit_code == unknown.exit_code == 0 and known.output == unknown.output
    assert password not in known.output
    assert alice.get('/api/conversations').status_code == 401
    assert (
        alice.post('/login', data={'email': 'alice@example.test', 'password': password}).status_code
        == 302
    )
    assert alice.get('/api/conversations').status_code == 200
    with app.app_context():
        assert db.session.scalar(db.select(User).where(User.name == 'alice')).auth_version == 2
