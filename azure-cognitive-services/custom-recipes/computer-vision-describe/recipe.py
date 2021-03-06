import os
import json
import dataiku
import requests
import pandas as pd
from dataiku.customrecipe import *
from azure_cognitive_services import *


#==============================================================================
# PLUGIN SETTINGS
#==============================================================================

# Input & output dataset
INPUT_FOLDER_NAME = get_input_names_for_role('input-folder')[0]
OUTPUT_DS_NAME = get_output_names_for_role('output-dataset')[0]

# Recipe settings
API_KEY = get_recipe_config()['api-key']
AZURE_LOCATION = get_recipe_config()['azure-location']
MAX_CANDIDATES = get_recipe_config().get('max-candidates', 1)
LANGUAGE = get_recipe_config()['language']


#==============================================================================
# INPUT
#==============================================================================

folder_dku  = dataiku.Folder( INPUT_FOLDER_NAME )
folder_info = folder_dku.get_info()
folder_path = folder_info["path"]


#==============================================================================
# QUERY API SERVICE
#==============================================================================

# Building base query URL and headers
endpoint = "https://{}.api.cognitive.microsoft.com/vision/v2.0".format(AZURE_LOCATION)
service  = "/describe"
full_url =  endpoint + service

headers = {
    'Content-Type': 'application/octet-stream',
    'Ocp-Apim-Subscription-Key': API_KEY
}

# Restricting image format 
ALLOWED_FORMATS = ['jpeg', 'jpg', 'png', 'gif', 'bmp']

# Actually building and submitting the query
o = []

for file in os.listdir(folder_path):
    
    # Query options
    options = {}
    options['language'] = LANGUAGE
    if MAX_CANDIDATES > 1:
        options['maxCandidates'] = int(MAX_CANDIDATES)
        
    # Query data
    extension = file.split(".")[-1].lower()
    d = {}
    d["directory_id"] = folder_info["id"]
    d["directory_path"] = folder_info["path"]
    d["file_name"] = file
    d["extension"] = extension
    if extension in ALLOWED_FORMATS:
        path = os.path.join(folder_path, file)
        image = open(path, "rb").read()
        r = requests.post(full_url, data=image, headers=headers, params=options)
        d["response"] = json.dumps(r.json())
    else:
        d["response"] = "(Dataiku) Format {} not allowed".format(extension)
    o.append(d)

        
#==============================================================================
# OUTPUT
#==============================================================================

ags_img = dataiku.Dataset(OUTPUT_DS_NAME)
ags_img.write_with_schema( pd.DataFrame(o) )