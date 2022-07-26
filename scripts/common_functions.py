# Copyright 2022 VMware, Inc.
# SPDX-License-Identifier: BSD-2-Clause

"""Common Functions
This file contains some common functions that are used within
the other scripts in this repo.

This file can also be imported as a module.
"""

def read_key(file_name):
    """Retrieves a GitHub API key from a file.
    
    Parameters
    ----------
    file_name : str

    Returns
    -------
    key : str
    """

    from os.path import dirname, join

    # Reads the first line of a file containing the GitHub API key
    # Usage: key = read_key('gh_key')

    current_dir = dirname(__file__)
    file2 = "./" + file_name
    file_path = join(current_dir, file2)

    with open(file_path, 'r') as kf:
        key = kf.readline().rstrip() # remove newline & trailing whitespace
    return key

def read_orgs(file_name):
    """Retrieves a list of orgs from a file.
    
    Parameters
    ----------
    file_name : str

    Returns
    -------
    org_list : list
    """
    import csv

    org_list = []

    with open(file_name) as orgfile:
        orgs = csv.reader(orgfile)
        for row in orgs:
            org_list.append(row[0])

    return org_list

def read_file(file_name):
    """Retrieves a list from a file.
    
    Parameters
    ----------
    file_name : str

    Returns
    -------
    a_list : list
    """
    import csv

    content_list = []

    with open(file_name) as in_file:
        content = csv.reader(in_file)
        for row in content:
            content_list.append(row[0])

    return content_list

def expand_name_df(df,old_col,new_col):
    """Takes a dataframe df with an API JSON object with nested elements in old_col, 
    extracts the name, and saves it in a new dataframe column called new_col

    Parameters
    ----------
    df : dataframe
    old_col : str
    new_col : str

    Returns
    -------
    df : dataframe
    """
    
    import pandas as pd

    def expand_name(nested_name):
        """Takes an API JSON object with nested elements and extracts the name
        Parameters
        ----------
        nested_name : JSON API object

        Returns
        -------
        object_name : str
        """
        if pd.isnull(nested_name):
            object_name = 'Not Found'
        else:
            object_name = nested_name['name']
        return object_name

    df[new_col] = df[old_col].apply(expand_name)
    return df
    


