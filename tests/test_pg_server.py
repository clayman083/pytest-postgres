import psycopg2


def test_pg_server(pg_server):
    with psycopg2.connect(**pg_server['params']) as conn:
        with conn.cursor() as cursor:
            cursor.execute('SELECT version();')
