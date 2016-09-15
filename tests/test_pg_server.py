import psycopg2


def test_pg_server(pg_server):
    pg_params = pg_server['pg_params']
    with psycopg2.connect(**pg_params) as conn:
        with conn.cursor() as cursor:
            cursor.execute('SELECT version();')
