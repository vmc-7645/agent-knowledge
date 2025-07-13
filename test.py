import psycopg2
dsn = "postgresql://postgres:password@127.0.0.1:6543/agentdb?sslmode=disable&gssencmode=disable"
conn = psycopg2.connect(dsn)
print("connected:", conn.get_dsn_parameters()['user'])
conn.close()
