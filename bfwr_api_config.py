# BigFix server URL and API route for JSON requests about computer information
url = "https://yourbfserver"
method = "/json/computers"
page = "/webreports?page=ExploreComputers"
out = "output.txt"

# Columns in order of appearance left to right (list of strings) 
# Properties from analyses should also append the name of their source analysis 
# in parentheses with no intervening space. 
# e.g. "Analysis Property(Analysis Name)"
# This information is in the column picker in Web Reports
#
# Also: you must always include "Computer Name"...
columns = ["Computer Name",
        "IP Address",
        "OS",
        "CPU",
        "Last Report Time",
        "Active Directory Path"]

# Column sorting precedence and direction (list of dicts)
# Sorting is not required on all columns
sorts = [{"column":"Computer Name","direction":"asc"},
        {"column":"Last Report Time","direction":"desc"},
        {"column":"IP Address","direction":"asc"}]

# Provide a list of columns to expand
# This removes the need to iterate over individual cells as arrays, but will create
# another row in your results by duplicating the rest of that row.
expansions = ["IP Address"]

