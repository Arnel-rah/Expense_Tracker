from app import create_app, db

app = create_app()

@app.cli.command('initdb')
def initdb_command():
    db.create_all()
    print('Base de données initialisée.')

if __name__ == '__main__':
    app.run(debug=True, ssl_context=('server.crt', 'server.key'), host='0.0.0.0', port=443)
