import psycopg2

# Establish database connection
try:
    connection = psycopg2.connect(user="postgres",
                                  password="postgres",
                                  host='127.0.0.1',
                                  port="5432",
                                  database="clinical")

    cursor = connection.cursor()
    # Print PostgreSQL Connection properties
    print(connection.get_dsn_parameters(), "\n")

    # Print PostgreSQL version
    cursor.execute("SELECT version();")
    record = cursor.fetchone()
    print("You are connected to - ", record, "\n")

except (Exception, psycopg2.Error) as error:
    print("Error while connecting to PostgreSQL", error)


# Execute & commit sql statement
# Rollback if error
def sql_exe(sql):
    try:
        cursor.execute(sql)
        connection.commit()

        print("SQL successful")
        return True

    except (Exception, psycopg2.Error) as error:
        connection.rollback()

        print(error)
        return False


sql = 'TRUNCATE TABLE public.\"Patient\", public.\"Event\", public.\"Value_nm\", public.\"Value_tx\", public.\"Relationship\" CASCADE;'
#sql = 'TRUNCATE TABLE public.\"Dictionary\" CASCADE;'

sql_exe(sql)

if (connection):
    cursor.close()
    connection.close()
    print("PostgreSQL connection is closed")