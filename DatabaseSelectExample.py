import psycopg2
import psycopg2.extras

# Establish database connection
try:
    connection = psycopg2.connect(user="postgres",
                                  password="postgres",
                                  host='127.0.0.1',
                                  port="5432",
                                  database="clinical")

    # The cursors are the database conncetion objects for executing SQL statements
    cursor = connection.cursor()
    dictionary_cursor = connection.cursor(cursor_factory=psycopg2.extras.DictCursor)

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


def sql_exe_dictionary(sql):
    try:
        dictionary_cursor.execute(sql)
        connection.commit()

        print("SQL successful")
        return True

    except (Exception, psycopg2.Error) as error:
        connection.rollback()

        print(error)
        return False


# This is the SQL statement you want to execute
# A few Examples of possible SQL querys are in the sql select example.txt

# Be careful about " and ' chars as you need to include them in the SQL statement
sql = '''SELECT * 
        FROM "Patient" INNER JOIN "Event" ON "Patient"."Pat_id" = "Event"."Pat_id"
        LEFT OUTER JOIN "Value_nm" ON "Event"."Event_id" = "Value_nm"."Event_id"
        LEFT OUTER JOIN "Value_tx" ON "Event"."Event_id" = "Value_tx"."Event_id";'''

print(sql)




# Using the cursor you can execute the SQL statement
# Accesing specific attributes in the return is done through indexes
# Meaning row[0] or row[1] ...
sql_exe(sql)
rows = cursor.fetchall()    # fetchall() gets all return rows, fetchmany(size) gets size amount of returned rows
                            # fetchone() gets one row of the returned rows


# Using the dictionary cursor gives you the ability to select attributes by name later on
# Meaning row['Event_id'] or row ['age'] ...
sql_exe_dictionary(sql)
rows = dictionary_cursor.fetchall()


# This will print the whole return of the SQL statement
print(rows)


# You can access the rows of the selected data using a for loop
for row in rows:
    print(row)

# Close database connection at the the of the program
if (connection):
    cursor.close()
    connection.close()
    print("PostgreSQL connection is closed")