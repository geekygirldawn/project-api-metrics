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

### Repository Activity
These scripts demonstrate the difference in speed and
rate limits between the GitHub REST API and the GraphQL API. The original
REST script took hours to run across our 60+ GitHub orgs and had to be
slowed down to avoid hitting the rate limit, while the GraphQL version,
which gathers the same data, runs in less than 15 minutes without hitting
any rate limits.

    scripts/repo_activity.py
    scripts/repo_activity_REST.py

We use this script at VMware to gather basic data about the repositories
found in dozens of VMware GitHub orgs. We use this to understand whether
projects are meeting our compliance requirements. We also use this 
script to find abandoned repos that have outlived their usefulness
and should be archived.

### Mystery GitHub Organizations

We use this script at VMware to gather basic data about GitHub orgs that
we believe may have been created outside of our process by various
employees across our business units. We gather the first few members
of the org to help identify employees who can provide more details
about the purpose of the org and how it is used.

    scripts/mystery_orgs.py

## Acceptable Use

Note: Some of these scripts gather names and email addresses, which we use 
to help us find a contact within VMware if we have questions about a 
repository or org. Note that the [GitHub Acceptable Use
Policies](https://docs.github.com/en/github/site-policy/github-acceptable-use-policies)
prohibits certain usage of information, and I would encourage you to read
this policy and not use scripts like these for unethical purposes.
