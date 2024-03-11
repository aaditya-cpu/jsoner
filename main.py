import pandas as pd
import requests
import logging
import re
import json
import ast
from logging.handlers import RotatingFileHandler

# Setup structured logging without external dependencies
class StructuredMessage:
    def __init__(self, message, **kwargs):
        self.message = message
        self.kwargs = kwargs

    def __str__(self):
        return f"{self.message} | {json.dumps(self.kwargs)}"

def setup_logging():
    logger = logging.getLogger()
    handler = RotatingFileHandler('process_requests.log', maxBytes=10485760, backupCount=5)
    logging.basicConfig(level=logging.INFO, handlers=[handler], format='%(asctime)s - %(levelname)s - %(message)s')

setup_logging()
logger = logging.getLogger(__name__)

def send_request(url, headers, payload):
    """Sends a POST request to the specified URL."""
    try:
        logger.info(StructuredMessage("Sending request", url=url, payload=payload))
        response = requests.post(url, headers=headers, data=json.dumps(payload))
        response.raise_for_status()  # Will raise HTTPError if the status is 4xx or 5xx
        logger.info(StructuredMessage("Received response", status_code=response.status_code, response=response.text[:100]))
        return response.json()  # Assuming response is in JSON format
    except requests.exceptions.RequestException as e:
        logger.error(StructuredMessage("Request failed", error=str(e)))
        return None

def process_example_field(example_str, text_template):
    """Converts the example field's string from CSV into a structured dict expected by the API."""
    try:
        # Convert the stringified list to an actual list
        examples_list = ast.literal_eval(example_str)

        # Parse placeholders (e.g., "{{1}}") from the text_template
        placeholders = re.findall(r'\{\{(\d+)\}\}', text_template)

        # Construct a dict using placeholders as keys
        example_data = {placeholders[i]: examples_list[i] for i in range(len(placeholders))}

        # Return the example in the expected format
        return {"example_data": example_data}
    except Exception as e:
        logger.error(StructuredMessage("Error processing 'example' field", error=str(e), example_str=example_str))
        return None

def process_and_send_requests(csv_file_path, url, headers):
    try:
        csv_data = pd.read_csv(csv_file_path)
    except Exception as e:
        logger.critical(StructuredMessage("Failed to read CSV file", error=str(e)))
        return

    for index, row in csv_data.iterrows():
        logger.debug(StructuredMessage("Processing row", row_index=index))

        # Initialize the components list
        components = []

        # If the row contains type and text columns, construct the component dict
        if pd.notna(row['type']) and pd.notna(row['text']):
            component = {
                "type": row['type'].strip(),
                "text": row['text'].strip()
            }
            
            # If the row has an 'example' column, process it
            if pd.notna(row['example']):
                example_data = process_example_field(row['example'], row['text'])
                if example_data:
                    component["example"] = example_data["example_data"]
            
            components.append(component)

        # Construct the payload for the POST request
        payload = {
            "name": row['name'].strip(),
            "category": row['category'].strip(),
            "allow_category_change": row['allow_category_change'],
            "language": row['language'].strip(),
            "components": components
        }

        # Send the request
        send_request(url, headers, payload)

# # Configuration (Ensure to replace placeholder token and file path)
# headers = {
#     'Content-Type': 'application/json',
#     'Authorization': 'Bearer YOUR_ACCESS_TOKEN'
# }
# url = "https://graph.facebook.com/v19.0/YOUR_PAGE_ID/message_templates"
# csv_file_path = '/path/to/your/csv_file.csv'

# # Execute the function
# process_and_send_requests(csv_file_path, url, headers)

headers = {
  'Content-Type': 'application/json',
  'Authorization': 'Bearer EAACcVRr4DOEBAIskJ14tm5GqC0B94LUlf9ZAlSbtZAyWzrDDyudVymiQs7WitAogW3qNAvGqe52lGNm2rUnuOB0ywsTorsAVnnP72VzTyTA6oiS5CNX4uWU3GvPedHbPUVigEDP2cvJagVlhMPq52bZBOQas7ZCfwaJvOxlzlunDK3g0xAbmu3e2SB9ckqKFA2wIYoeqKQZDZD',
  'Cookie': 'ps_l=0; ps_n=0'
}
url = "https://graph.facebook.com/v19.0/118164994591593/message_templates"
csv_file_path = 'jsons.csv' 
# Execute the function
process_and_send_requests(csv_file_path, url, headers)
 # Path to your CSV file

# Execute the function
# process_and_send_requests(csv_file_path, url, headers)