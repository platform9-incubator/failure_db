# failure_db
Hackathon idea about automated failure analysis

# Benefits
- Intelligent mapping of failures to Jira based on md5 signature of failures
- Less likelihood of failures going unnoticed
- Ability to find Bug reoccurrences to help prioritize fixing
- Help save engineers effort to triage failures which already exist in Jira
- Single pane of view to see all failures and their respective Bugs

# Solution overview
- Central MySQL DB to track all test automation failures
- Teamcity integration to populate test failure data via REST APIs
- Web-based GUI to show list of failures and map them against Jira
- Automated mapping of test failures to known Bugs
