# Copyright 2022 VMware, Inc.
# SPDX-License-Identifier: BSD-2-Clause

"""Mystery Orgs
This script uses the GitHub GraphQL API to retrieve relevant
information about one or more GitHub orgs.

We use this script at VMware to gather basic data about GitHub orgs that
we believe may have been created outside of our process by various
employees across our business units. We gather the first few members
of the org to help identify employees who can provide more details
about the purpose of the org and how it is used.

As input, this script requires a file named 'orgs.txt' containing
the name of one GitHub org per line residing in the same folder 
as this script.

Your API key should be stored in a file called gh_key in the
same folder as this script.

As output:
* A message about each org being processed will be printed to the screen.
* the script creates a csv file stored in an subdirectory
  of the folder with the script called "output" with the filename in 
  this format with today's date.

output/mystery_orgs_2022-01-14.csv"
"""

import sys
from common_functions import read_key

def make_query():
    """Creates and returns a GraphQL query"""
    return """query OrgQuery($org_name: String!) {
             organization(login:$org_name) {
               name
               url
               websiteUrl
               createdAt
               updatedAt
               membersWithRole(first: 15){
                 nodes{
                   login
                   name
                   email
                   company
                 }
               }
              }
            }"""

# Read GitHub key from file using the read_key function in 
# common_functions.py
try:
    api_token = read_key('gh_key')

except:
    print("Error reading GH Key. This script depends on the existance of a file called gh_key containing your GitHub API token. Exiting")
    sys.exit()

def get_org_data(api_token):
    """Executes the GraphQL query to get org data from one or more GitHub orgs.

    Parameters
    ----------
    api_token : str
        The GH API token retrieved from the gh_key file.

    Output
    -------
    Writes a csv file of the form 'mystery_orgs_2022-16-01.csv' with today's date
    """

    import requests
    import json
    import sys
    import csv
    from datetime import datetime
    from common_functions import read_orgs, create_file

    url = 'https://api.github.com/graphql'
    headers = {'Authorization': 'token %s' % api_token}
    
    # Read list of orgs from a file
    try:
        org_list = read_orgs('orgs.txt')
    except:
        print("Error reading orgs. This script depends on the existance of a file called orgs.txt containing one org per line. Exiting")
        sys.exit()

    # Initialize list of lists with a header row.
    # Each embedded list will become a row in the csv file
    all_rows = [['org_name', 'org_url', 'website', 'org_createdAt', 'org_updatedAt', 'people(login,name,email,company):repeat']]
    
    for org_name in org_list:

        print("Processing", org_name)

        row = []
        query = make_query()

        variables = {"org_name": org_name}
        r = requests.post(url=url, json={'query': query, 'variables': variables}, headers=headers)
        json_data = json.loads(r.text)

        # Take the json_data file and expand the info about people horizontally into the 
        # same row as the rest of the data about that org.  
        try:      
            for key in json_data['data']['organization']:
                if key == 'membersWithRole':
                    for nkey in json_data['data']['organization'][key]['nodes']:
                        row.append(nkey['login'])
                        row.append(nkey['name'])
                        row.append(nkey['email'])
                        row.append(nkey['company'])
                else:
                    row.append(json_data['data']['organization'][key])
            all_rows.append(row)
        except:
            pass
        
    # prepare file and write rows to csv

    try:
        file = create_file("mystery_orgs")

        with file:    
            write = csv.writer(file)
            write.writerows(all_rows)

    except:
        print('Could not write to csv file. This may be because the output directory is missing or you do not have permissions to write to it. Exiting')

get_org_data(api_token)
