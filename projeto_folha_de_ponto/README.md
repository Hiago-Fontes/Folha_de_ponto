Projeto Folha de Ponto - notas rápidas

- Problema resolvido: erro "Table 'employee' is already defined" causado por import circular/definição múltipla do objeto `db`.
- Solução: criei `extensions.py` com `db = SQLAlchemy()` e passei a inicializar com `db.init_app(app)` em `app.py`. Os modelos agora importam `db` de `extensions`.

Como testar rapidamente:

1. Ative seu virtualenv e execute:

	C:/Users/hiago/OneDrive/Documentos/PacMan/projeto_folha_de_ponto/.venv/Scripts/python.exe -m scripts.test_db

Deverá ver a saída:

found: <Employee TEST_CHECK>
teste concluido

