from app import create_app

app = create_app()

if __name__ == '__main__':
    import os
    app.run(host='127.0.0.1', port=int(os.environ.get('PORT') or 8000), debug=False)
