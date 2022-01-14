# Python Scripts

These Python 3 scripts use the GitHub APIs to gather data.

## Requirements:

The scripts all have a few common requirements, and individual
scripts may have additional requirements and other information
which can be found in the Docstrings.

* These scripts require that `pandas` be installed within the Python
  environment you are running this script in.
* Your API key should be stored in a file called gh_key in the
  same folder as these scripts.
* Most scripts require that a folder named "output" exists in this
  scripts directory, and csv output files will be stored there.

## Scripts

The first 2 scripts in this repo demonstrate the difference in speed and
rate limits between the GitHub REST API and the GraphQL API. The original
REST script took hours to run across our 60+ GitHub orgs and had to be
slowed down to avoid hitting the rate limit, while the GraphQL version,
which gathers the same data, runs in less than 15 minutes without hitting
any rate limits.

    scripts/repo_activity.py
    scripts/repo_activity_REST.py

Note: These scripts gather names and email addresses of
committers, which we use to help us find a contact within VMware if we
have questions about a repository. Note that the [GitHub Acceptable Use
Policies](https://docs.github.com/en/github/site-policy/github-acceptable-use-policies)
prohibits certain usage of information, and I would encourage you to read
this policy and not use scripts like these for unethical purposes.
