#!/usr/bin/env python

# Copyright 2022 VMware, Inc.
# SPDX-License-Identifier: BSD-2-Clause
# Author: Dawn M. Foster <fosterd@vmware.com>

"""GitHub Organization Access Audit
This script uses the GitHub GraphQL API to retrieve relevant
information about all enterprise owners and org members from 
one or more GitHub orgs.

Note that you must have appropriate access to this data in the
orgs requested. Missing data likely means that you don't have
access.

As input, this script requires a file named 'orgs.txt' containing
the name of one GitHub org per line residing in the same folder 
as this script.

Your API key should be stored in a file called gh_key in the
same folder as this script.

As output:
* JSON data is currently printed to the screen as way to do this
  quickly.
"""

import sys
from common_functions import read_key

def make_query(after_cursor = None):
    """Creates and returns a GraphQL query with cursor for pagination"""

    return """query ($org_name: String!){
  organization(login: $org_name){
    url
    enterpriseOwners(first:100){
      nodes{
        login
      }
    }
    membersWithRole(first:100){
      nodes{
        login
        name
      }
    }
  }
}
"""

# Read GitHub key from file using the read_key function in 
# common_functions.py
try:
    api_token = read_key('gh_key')

except:
    print("Error reading GH Key. This script depends on the existance of a file called gh_key containing your GitHub API token. Exiting")
    sys.exit()

def get_org_data(api_token):
    """Executes the GraphQL query to get owner / member data from one or more GitHub orgs.

    Parameters
    ----------
    api_token : str
        The GH API token retrieved from the gh_key file.

    Returns
    -------
    repo_info_df : pandas.core.frame.DataFrame
    """
    import requests
    import json
    import pandas as pd
    from common_functions import read_orgs
    import sys

    url = 'https://api.github.com/graphql'
    headers = {'Authorization': 'token %s' % api_token}
    
    # Read list of orgs from a file

    try:
        org_list = read_orgs('orgs.txt')
    except:
        print("Error reading orgs. This script depends on the existance of a file called orgs.txt containing one org per line. Exiting")
        sys.exit()
    
    for org_name in org_list: 
        try:
            query = make_query()

            variables = {"org_name": org_name}
            r = requests.post(url=url, json={'query': query, 'variables': variables}, headers=headers)
            json_data = json.loads(r.text)

            print(json_data)
        except:
            print("ERROR Cannot process", org_name)
    
get_org_data(api_token)

