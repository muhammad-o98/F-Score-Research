from dotenv import load_dotenv
import os
import csv
from notion_client import Client

# -------------------------------
# Load environment variables
# -------------------------------
load_dotenv()
NOTION_TOKEN = os.getenv("NOTION_TOKEN")

# -------------------------------
# Initialize Notion client
# -------------------------------
notion = Client(auth=NOTION_TOKEN)

# -------------------------------
# Query database
# -------------------------------
def fetch_database_rows(database_id):
    results = []
    start_cursor = None

    while True:
        response = notion.databases.query(
            database_id=database_id,
            start_cursor=start_cursor
        )
        results.extend(response["results"])

        if not response.get("has_more"):
            break
        start_cursor = response.get("next_cursor")
    
    return results

# -------------------------------
# Extract row data (flatten properties)
# -------------------------------
def parse_row(page):
    data = {}
    properties = page["properties"]
    for key, value in properties.items():
        prop_type = value["type"]

        if prop_type == "title":
            data[key] = "".join([t["plain_text"] for t in value["title"]])
        elif prop_type == "rich_text":
            data[key] = "".join([t["plain_text"] for t in value["rich_text"]])
        elif prop_type == "select":
            data[key] = value["select"]["name"] if value["select"] else ""
        elif prop_type == "multi_select":
            data[key] = ", ".join([v["name"] for v in value["multi_select"]])
        elif prop_type == "checkbox":
            data[key] = value["checkbox"]
        elif prop_type == "number":
            data[key] = value["number"]
        elif prop_type == "date":
            data[key] = value["date"]["start"] if value["date"] else ""
        elif prop_type == "people":
            data[key] = ", ".join([p["name"] for p in value["people"]])
        else:
            data[key] = str(value.get(prop_type))  # Fallback
    return data

# -------------------------------
# Save to CSV
# -------------------------------
def save_to_csv(data, csv_path):
    if not data:
        print(f"⚠️ No data to write for {csv_path}.")
        return

    os.makedirs(os.path.dirname(csv_path), exist_ok=True)

    fieldnames = data[0].keys()

    with open(csv_path, mode="w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        for row in data:
            writer.writerow(row)

    print(f"✅ Data saved to {csv_path}")

# -------------------------------
# Define your database → CSV mapping
# -------------------------------
def get_db_csv_mapping():
    # Manually map environment vars here
    return {
        "Scenario Bank": {
            "database_id": os.getenv("DB_SCENARIO_BANK"),
            "csv_path": os.getenv("CSV_SCENARIO_BANK")
        }#,
        #"Task List": {
        #    "database_id": os.getenv("DB_TASK_LIST"),
        #    "csv_path": os.getenv("CSV_TASK_LIST")
        #}
        # Add more here as needed
    }

# -------------------------------
# Main script
# -------------------------------
if __name__ == "__main__":
    dbs = get_db_csv_mapping()

    for label, config in dbs.items():
        print(f"\n📦 Processing '{label}'...")
        db_id = config["database_id"]
        csv_path = config["csv_path"]

        if not db_id or not csv_path:
            print(f"❌ Skipping '{label}': missing database ID or CSV path.")
            continue

        pages = fetch_database_rows(db_id)
        parsed_data = [parse_row(page) for page in pages]
        save_to_csv(parsed_data, csv_path)
