# import pandas as pd
# import json
# import ast

# def safe_strip(value):
#     """Safely strip string values, return empty string for non-strings."""
#     return value.strip() if isinstance(value, str) else ''
# def csv_to_json_and_write_safe(file_path, output_file_path):
#     # Load the CSV data
#     csv_data = pd.read_csv(file_path)
    
#     # Prepare a list to hold each message's JSON structure
#     json_messages = []
    
#     for _, row in csv_data.iterrows():
#         # Basic information, using safe_strip to handle non-string values
#         message_json = {
#             "name": safe_strip(row["name"]),
#             "category": safe_strip(row["category"]),
#             "allow_category_change": row["allow_category_change"],
#             "language": safe_strip(row["language"]),
#             "components": []
#         }
        
#         # Handle the BODY component
#         body_component = {
#             "type": "BODY",
#             "text": safe_strip(row["text"]),
#             "example": {"body_text": []}  # Initialize to empty list by default
#         }
        
#         # Attempt to parse the `example` field, catch SyntaxError for manual review
#         try:
#             body_component["example"]["body_text"] = ast.literal_eval(row["example"])
#         except (ValueError, SyntaxError) as e:
#             print(f"Manual review needed for {row['name']}: {e}")
        
#         message_json["components"].append(body_component)
        
#         # Handle the FOOTER component
#         if 'type.1' in row and 'text.1' in row and pd.notnull(row['type.1']) and pd.notnull(row['text.1']):
#             footer_component = {
#                 "type": safe_strip(row["type.1"]),
#                 "text": safe_strip(row["text.1"])
#             }
#             message_json["components"].append(footer_component)
        
#         # Append to the list of messages
#         json_messages.append(message_json)
    
#     # Convert to JSON string
#     json_output = json.dumps(json_messages, indent=4)
    
#     # Write to the specified output file
#     with open(output_file_path, 'w') as f:
#         f.write(json_output)

# # Re-define file paths
# input_file_path = 'jsons.csv'
# output_file_path = 'structured_messages_safe.json'

# # Call the function with the updated logic
# csv_to_json_and_write_safe(input_file_path, output_file_path)

# # Returning the path to the output file
# output_file_pathimport pandas as pdimport pandas as pd
import pandas as pd
import json
import requests
import logging
import ast

# Configure logging to write to a file with detailed information
logging.basicConfig(filename='process_requests.log', filemode='w', level=logging.INFO,
                    format='%(asctime)s - %(levelname)s - %(message)s')

def send_request(url, headers, payload):
    """
    Sends a POST request to the specified URL with the given headers and JSON payload.
    
    Args:
        url (str): The URL to which the request is sent.
        headers (dict): The headers to include in the request, such as 'Content-Type' and 'Authorization'.
        payload (str): The JSON payload as a string to be sent in the request.
        
    Returns:
        str: The response text from the server, detailing success or failure of the request.
    """
    try:
        logging.info(f"Sending request to {url} with payload: {payload}")
        response = requests.post(url, headers=headers, data=payload)
        logging.info(f"Received response: {response.text}")
        return response.text
    except requests.exceptions.RequestException as e:
        logging.error(f"Request failed: {e}")
        return None

def process_example_field(example_str):
    """
    Safely evaluates the string from the CSV's 'example' column into a Python object,
    ensuring it matches the expected structure for the API request.
    
    Args:
        example_str (str): The example field as a string from the CSV.
    
    Returns:
        list or dict: The 'example' field converted into a Python object.
    """
    try:
        example_obj = ast.literal_eval(example_str)
        return example_obj
    except (ValueError, SyntaxError) as e:
        logging.error(f"Error processing example field: {e}")
        return []

def process_and_send_requests(csv_file_path, url, headers):
    """
    Processes each row of the CSV file, constructs and sends requests to the Facebook API.
    
    Args:
        csv_file_path (str): Path to the CSV file containing the message template data.
        url (str): The API endpoint URL for sending message templates.
        headers (dict): The request headers including Authorization token.
    """
    csv_data = pd.read_csv(csv_file_path)
    
    for index, row in csv_data.iterrows():
        logging.info(f"Processing row {index}")
        example_body_text = process_example_field(row['example'])
        components = [{
            "type": row['type'],
            "text": row['text'],
            "example": example_body_text  # This should be adjusted according to the specific structure required by the API.
        } for _, row in csv_data.iterrows()]
        
        payload = {
            "name": row['name'].strip(),
            "category": row['category'].strip(),
            "allow_category_change": row['allow_category_change'],
            "language": row['language'].strip(),
            "components": components
        }
        
        json_payload = json.dumps(payload)
        response = send_request(url, headers, json_payload)
        if response:
            logging.info(f"Response for row {index}: {response}")
        else:
            logging.error(f"Failed to get a response for row {index}.")

# API and CSV file configuration
headers = {
    'Content-Type': 'application/json',
    'Authorization': 'Bearer YOUR_ACCESS_TOKEN',
    'Cookie': 'ps_l=0; ps_n=0'
}
url = "https://graph.facebook.com/v19.0/118164994591593/message_templates"
csv_file_path = 'jsons.csv'  # Update with the correct path to your CSV file

# Execute the function with the provided parameters
process_and_send_requests(csv_file_path, url, headers)
