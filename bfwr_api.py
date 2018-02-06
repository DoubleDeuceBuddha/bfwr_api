import cookielib
import json
import urllib,urllib2
import ssl
import getpass
import re

# Config file is bfwr_api_config.py
import bfwr_api_config as cfg

# This demonstrates some of the new APIs backing the BigFix Web Reports JS frontend
# First, it pulls some of the predefined filters, properties, groups, etc that are
# supplied within the initial login and load of the Explore Computers page and prints
# them. It then does a very basic pull from the /json/computers APImethod, demonstrating column
# selection, result count, pagination, and column sorting, and prints those results as well.
#
# Confirmed works with python 2.7.14

# Load settings from config file
bigfix_url = cfg.url
computers_method = cfg.method
explore_computers_page = cfg.page
columns = cfg.columns
sorts =  cfg.sorts
expansions = cfg.expansions

# Open output file
outfile = open(cfg.out, "w")

# Since the most relevant information in most of the JSON objects
# pulled out of the web page's JS is in the "id" and "name" properties, 
# process_json is geared towards that. If you're curious, stepping 
# over a search of the source from your ExploreComputers page for 
# "WR.Filters." will show you a few of the things Web Reports pre-loads. 
# The function parameters are primarily to accommodate differences
# in the pre-load objects' data structures.
def process_json(js_line,js_variable,pretty_name,match_string="];",replace_string="]",sub_prop=None):
    prop_load = json.loads(js_line.replace("WR."+ js_variable + " = ","").replace(match_string,replace_string))

    result_dict = {}

    if sub_prop:
        props = prop_load[sub_prop]
    else:
        props = prop_load

    for result in props:
        if ("id" in result) and ("name" in result):
            if ("analysis" in result):
                result_dict[result["name"] + "(" + result["analysis"]["name"]  + ")"] = result["id"]
            else:            
                result_dict[result["name"]] = result["id"]
    return result_dict
    
# Build parameters from information provided
def build_parameters(columns,sorts,computer_props):
    parameters = ""

    for column in columns:
        parameters += "&c=" + computer_props[column]
    for sort_parm in sorts:
        parameters += "&sort=" + computer_props[sort_parm["column"]] + "&dir=" + sort_parm["direction"]
    for expand in expansions:
        parameters += "&expandColumn=" + computer_props[expand]

    parameters += "&results=-1&startIndex=0"
    complete_parms = urllib.quote(re.sub(r"^&c=","?c=",parameters),"/=&?")
    return complete_parms

# Get results - setting clean to True will replace any inline commas with pipes
def fetch_results(machine,property,clean=False):
    if "result" in machine["properties"][property]:
        if machine["properties"][property]["plural"]:
            property_list_length = len(machine["properties"][property]["result"])
            if property_list_length == 0:
                return ""
            else:
                concat_property = ""
                property_item_position = 0
                for property_item in machine["properties"][property]["result"]:
                    property_item_position += 1
                    concat_property += property_item
                    if property_item_position < property_list_length:
                        concat_property += "|"
                if clean:
                    return concat_property.replace(",","|")
                else:
                    return concat_property
        else:
            if clean:
                return machine["properties"][property]["result"].replace(",","|")
            else:
                return machine["properties"][property]["result"]
    else:
        return ""

def main():

    # Cookies for authentication
    cookie_jar = cookielib.CookieJar()

    # Skip validation of certs (lazy)
    # If you want to do it all fancy-like, you can go the cacerts route
    # described here https://wiki.python.org/moin/SSL
    ctx = ssl.create_default_context()
    ctx.check_hostname = False
    ctx.verify_mode = ssl.CERT_NONE

    # Set up and install URL opener
    bigfix_opener = urllib2.build_opener(urllib2.HTTPSHandler(context=ctx),urllib2.HTTPCookieProcessor(cookie_jar))
    urllib2.install_opener(bigfix_opener)

    # Get username and password, rawinput allows for special characters
    user = raw_input("Username? ").encode("UTF-8")
    credential = getpass.getpass("Password? ").encode("UTF-8")

    # Build and encode your raw data in a dict for submission in your http request
    login_raw_data = {
        "page": "LoggingIn",
        "fwdpage": "",
        "Username": user,
        "Password": credential
        }
    login_data = urllib.urlencode(login_raw_data)

    # Open your login page, get your cookie
    try:
        req = urllib2.Request(bigfix_url,login_data)
        resp = urllib2.urlopen(req)
        contents = resp.read()
    except urllib2.HTTPError,e:
        print "Failed with code: " + e
        sys.exit(1)

    # Open the ExploreComputers page and get its contents
    computer_properties_page = urllib2.Request(bigfix_url + explore_computers_page)
    properties_resp = urllib2.urlopen(computer_properties_page)
    properties_contents = properties_resp.read()

    # Parse the embedded JavaScript from the ExploreComputers page for
    # interesting information (e.g. the filters, properties, groups, etc
    # in use in your BigFix installation)
    for line in properties_contents.splitlines():
        if line.startswith("WR.Filters.FixletProperties = "):
            fixlet_props = process_json(line,"Filters.FixletProperties","Fixlet Properties")

        if line.startswith("WR.Filters.ActionProperties = "):
            action_props = process_json(line,"Filters.ActionProperties","Action Properties")

        if line.startswith("WR.Filters.ActionResultStatuses = "):
            action_result_statuses = process_json(line,"Filters.ActionResultStatuses","Action Results Statuses")

        if line.startswith("WR.Filters.DatabaseNames = "):
            db_names = process_json(line,"Filters.DatabaseNames","Database Names")

        if line.startswith("WR.Filters.SiteNames = "):
            site_names = process_json(line,"Filters.SiteNames","Site Names")

        if line.startswith("WR.Filters.ComputerGroups = "):
            computer_groups = process_json(line,"Filters.ComputerGroups","Computer Groups")

        if line.startswith("WR.ComputerProperties = "):
            computer_props = process_json(line,"ComputerProperties","Computer Properties",".results;","","results")

    # Pull down some raw computers data using the API

    # Use build_parameters to get your query string
    encoded_parms = build_parameters(columns,sorts,computer_props)

    # Make request
    result_req = urllib2.Request(bigfix_url + computers_method + encoded_parms)
    json_payload = json.load(urllib2.urlopen(result_req))

    # Parse through some of the columns and print them. For simplicity's sake, 
    # multi-result cells can have pipes replacing commas for lazy/easy parsing
    # The "plural" attribute of the property indicates whether it is an array.

    # This block included in comments in case you don't want to bother with custom
    # and just need a straight report
    #add_comma=0
    #for label in columns:
    #    outfile.write(label)
    #    add_comma+=1
    #    if add_comma < len(columns):
    #        outfile.write(",")
    #    else:
    #        outfile.write("\n")

    outfile.write("Computer Name, IP Address, /24 Subnet, AD Path, AD OU or Container, Last Report Date, Last Report Time\n")

    for machine in json_payload["results"]:
        report_line = fetch_results(machine,computer_props["Computer Name"]) + ","

        ip_address = fetch_results(machine,computer_props["IP Address"])
        report_line += ip_address + ","

        # Get /24 subnet for grouping
        report_line += re.sub(r"(?P<subn>(?:[0-9]{1,3}\.){3})[0-9]{1,3}","\g<subn>0/24",ip_address) + ","

        ad_path = ""
        ad_path = fetch_results(machine,computer_props["Active Directory Path"],True)
        report_line += ad_path + ","

        # Get parent OU or container for AD abject
        if "OU=" in ad_path:
            report_line += "OU=" + ad_path.split("OU=",1)[1] + ","
        elif "CN=" in ad_path:
            report_line += "CN=" + ad_path.rsplit("CN=",1)[1] + ","
        else:
            report_line += ad_path + ","

        # Split into date and time
        report_line += re.sub(r"(Mon|Tue|Wed|Thu|Fri|Sat|Sun), (\d\d) (Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec) (\d\d\d\d) (\d\d:\d\d:\d\d) \+\d\d\d\d",r"\2 \3 \4,\5",fetch_results(machine,computer_props["Last Report Time"]))

        outfile.write(report_line + "\n")

    outfile.close()

if __name__ == "__main__":
    main()
