from datetime import datetime
from metacat.webapi import MetaCatClient
import os
import json
import re


def format_timestamp(timestamp):
    if timestamp:
        return datetime.fromtimestamp(timestamp).strftime('%Y-%m-%d %H:%M:%S')
    return ''


with open(os.path.join(os.path.dirname(__file__), '..', 'config', 'tabsConfig.json')) as f:
    tabs_config = json.load(f)


class MetaCatAPI:
    def __init__(self):
        self.client = MetaCatClient(
            os.getenv('METACAT_SERVER_URL'),
            os.getenv('METACAT_AUTH_SERVER_URL')
        )

    def login(self, username, password):
        try:
            token = self.client.login_password(username, password)
            return {"success": True, "token": token}
        except Exception as e:
            return {"success": False, "message": str(e)}

    def get_datasets(self, query_text, category, tab, official_only):
        try:
            # Get the namespace based on tab and category
            namespace = next(
                (cat['namespace'] for cat in tabs_config[tab]['categories'] if cat['name'] == category),
                None
            )
            if not namespace:
                raise ValueError(f"No matching namespace found for tab '{tab}' and category '{category}'")

            # Construct the base MQL query
            mql_query = f"datasets matching {namespace}:*"

            having_conditions = []

            # Add search condition if query_text is provided
            if query_text:
                escaped_query = re.escape(query_text.replace("'", "\\'"))
                having_conditions.append(f"name ~* '(?i){escaped_query}'")

            if official_only:
                having_conditions.append("name ~* '(?i)official'")

            if having_conditions:
                mql_query += " having " + " and ".join(having_conditions)

            print(f"Executing MQL query: {mql_query}")  # Debug print

            results = self.client.query(mql_query)
            # print("Raw query results:")
            raw_results = list(results)  # Convert generator to list
            # for result in raw_results:
            #     print(result)  # Print each raw result

            formatted_results = [
                {
                    "name": result.get("name", ""),
                    "creator": result.get("creator", ""),
                    "created": format_timestamp(result.get("created_timestamp", "")),
                    "files": result.get("file_count", 0),
                    "namespace": namespace
                }
                for result in raw_results
            ]
            # print("Formatted query results:")
            # for result in formatted_results:
            #     print(result)  # Print each formatted result
            return {"success": True, "results": formatted_results}
        except Exception as e:
            print(f"Query error: {str(e)}")  # Debug print
            return {"success": False, "message": str(e)}

    def list_datasets(self):
        # This method is used for connection testing
        try:
            datasets = self.client.list_datasets()
            return {"success": True, "datasets": datasets}
        except Exception as e:
            return {"success": False, "message": str(e)}

    def get_files(self, namespace: str, name: str):
        try:
            mql_query = f"files from {namespace}:{name} limit 1000"
            print(f"Executing MQL query: {mql_query}")
            results = self.client.query(mql_query)
            raw_results = list(results)
            # print(f"Raw query results:")
            # for result in raw_results:
            #     print(result)
            files = [
                {
                    "fid": result.get("fid", ""),
                    "name": result.get("name", ""),
                    "updated": format_timestamp(result.get("updated_timestamp", "")),
                    "created": format_timestamp(result.get("created_timestamp", "")),
                    "size": result.get("size", result.get("size", 0)),
                }
                for result in raw_results
            ]

            return {"success": True, "files": files}
        except Exception as e:
            return {"success": False, "message": str(e)}
