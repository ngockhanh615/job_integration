import psycopg2
from psycopg2 import sql

# Database connection parameters
db_params = {
    'dbname': 'jobs',
    'user': 'postgres',
    'password': 'postgres',
    'host': '10.100.21.125',
    'port': '5432'
}

# Connect to PostgreSQL database
conn = psycopg2.connect(**db_params)
cur = conn.cursor()

# Query to fetch location data from global table
fetch_query = "SELECT id, location, source FROM global"

# Fetch data from global table
cur.execute(fetch_query)
global_data = cur.fetchall()

# Query to fetch province and district information
fetch_province_query = "SELECT ma, ten FROM provinces"
fetch_district_query = "SELECT ma, ten, matp FROM district"

cur.execute(fetch_province_query)
provinces = cur.fetchall()
province_dict = {prov[1]: str(int(prov[0])) for prov in provinces}

cur.execute(fetch_district_query)
districts = cur.fetchall()
district_dict = {(str(int(dist[2])), dist[1]): str(int(dist[0])) for dist in districts}
print(district_dict)

# Prepare to insert into location_mapping table
insert_query = """
    INSERT INTO location_mapping (global_id, province_id, district_id)
    VALUES (%s, %s, %s)
    ON CONFLICT (global_id, province_id, district_id) DO NOTHING
"""

# Function to extract province and district based on source
def extract_location(location, source):
    try:
        location_parts = location.split(', ')
        print(location_parts)
        
        if source == 'topcv.vn':
            province_name = location_parts[0].split(':')[0][1:].strip()
        elif source == 'careerviet.vn':
            province_name = location.strip()
        elif source == 'topdev.vn':
            province_name = location_parts[-1].strip()
        else:
            return None, None
        print(province_name)
        
        # Add "Thành phố" for specific cities
        if province_name in ["Hà Nội", "Hải Phòng", "Đà Nẵng", "Hồ Chí Minh", "Cần Thơ"]:
            province_name = "Thành phố " + province_name
        else:
            province_name = "Tỉnh " + province_name
        
        province_id = province_dict.get(province_name)
        print(province_id)
        if not province_id:
            print(f"Province '{province_name}' not found.")
            return None, None
        
        district_name = None
        if source == 'topcv.vn':
            district_name = location_parts[-1].strip()
        elif source == 'topdev.vn':
            district_name = location_parts[-2].strip()
        
        if "TP" in district_name:
            district_name = district_name.replace("TP", "Thành phố")
        print(district_name)
        
        # Try to get the district_id
        district_id = district_dict.get((str(int(province_id)), district_name)) if district_name else None
        
        # If district_id not found, try adding prefixes
        if not district_id and district_name:
            prefixes = ["Quận", "Huyện", "Thành phố", "Thị xã"]
            for prefix in prefixes:
                name = f"{prefix} {district_name}"
                print(name)
                district_id = district_dict.get((str(int(province_id)), name))
                if district_id:
                    break
        
        print(district_id)
        return province_id, district_id
    except Exception as e:
        print(f"Error extracting location for {source}: {location} - {e}")
        return None, None

# Extract and insert mappings
for global_id, location, source in global_data:
    try:
        province_id, district_id = extract_location(location, source)
        if province_id and district_id:
            print(insert_query, (global_id, province_id, district_id))
            cur.execute(insert_query, (global_id, province_id, district_id))
    except Exception as e:
        print(f"Error inserting mapping for global_id {global_id}: {e}")

# Commit the transaction
conn.commit()

# Close the connection
cur.close()
conn.close()
