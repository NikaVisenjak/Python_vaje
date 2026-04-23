from influxdb import InfluxDBClient

host = '127.0.0.1'#povezi na dejanskega ne lokalnega
user = 'guest'
password = 'guest'
port = 8086
DATABASE = 'test_db'

client = InfluxDBClient(host, port, user, password)
print(client.get_list_database())
client.create_database(DATABASE)
client.switch_database(DATABASE)

# client.query('DROP MEASUREMENT temperature')

points = []

with open('temperature_data.txt', 'r') as f:
    for i, line in enumerate(f):
        line = line.strip()
        if not line:
            continue

        temp1, temp2, cas, oseba = line.split(',')

        point = {
            "measurement": "temperature",
            "tags": {
                "oseba": oseba
            },
            "fields": {
                "temp1": float(temp1),
                "temp2": float(temp2),
                "cas": int(cas)
            }
        }

        points.append(point)

client.write_points(points)
print("Upload OK:", len(points))

# =========================
# CHECK
# =========================

print("\nMEASUREMENTS:")
print(client.query("SHOW MEASUREMENTS"))

print("\nTEST EVA < 0")
query = """
SELECT temp2
FROM temperature
WHERE oseba='Eva' AND temp2 < 0
"""

res = client.query(query)
rows = list(res.get_points())

print("Rezultatov:", len(rows))
for r in rows:
    print(r)