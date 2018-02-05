# Python script demonstrating BigFix Web Reports JSON APIs
### From BigFix 9.5.8

I noticed post-upgrade to 9.5.8 that some of the .csv methods were a little different (borked) from prior automation. Requests we had cadged from prior XHR and console watching to make our report automation simpler were no longer quite right...specifically the processes of applying a third and/or fourth dimension of fixlet information data to our first and second dimensions of computer properties data which we had been merging using bash (grep/sed/awk/cut/tr/etc,etc.) Digging into the XHR, we saw new methods in Web Reports, pretty clearly put there to support a deeper RESTful API integration and JS-ifying of the WR frontend vs the current core RESTful relevance-y XML . If you are like me and don't want to write a relevance for every single reporting activity, this is a magnificent savior for your sanity and productivity.

New methods (non-exhaustive):  

1.  computers
2.  fixletproperties
3.  chartdata
4.  getallfilters

All of these are accessible via http(s)://yourbfserver(:52311)/json/methodname

There are other filters oriented post methods (http(s)://yourbfserver(:52311)/post/methodname that are useful, but we'll only look at:  

1.  shortentext 

The parameters are set up as query arguments, once the list of parameters gets long enough, Web Reports has methods in its JavaScript to shorten them (/post/shortentext where formdata is the query list urlencoded and ?ShortenedParams= where the parameter is the response string handed you by  shortentext.) The results all live in the BESReporting DB, in dbo.SHORTENED_TEXT. The parameters are stored as the image datatype (hex representation) in the FullText column, and the ShortText column is a SHA1 hash of the ShortText. These should be unique values (e.g. no duplicates) but there is no datestamp or tracking to determine whether a shortened parameter list is still in use, so the table will never be cleaned up or otherwise managed for size.

 If you note 40 character hexadecimal strings in XHR requests/responses, they are likely the sha1sum keys stored in this table to reference your shortened text.

*   Example parameters that utilize this shortentext process are (not necessarily exhaustive):  
    filterManager  
    reportInfo  
    contentTable  
    chartSection  
    collapseState  


The code in this repo primarily uses the computers method, though it looks like many of the query parameters work universally.

Something else interesting is that the initial pageload of http(s)://yourbfserver(:52311))/webreports?page=ExploreComputers includes embedded JavaScript with a whole host of useful information which is used to population options, tables, and dropdowns. It isn't exactly straightforward to extract, but that's OK, because I put something together to do it for you. The information it includes in the pageload is contained in JSON objects as follows:

*   ActionProperties:
    * name  
    * id  

*   ActionResultStatuses:
    * name  
    * id  

*   ComputerGroups:
    * name  
    * id  

*   ComputerProperties:
    * name  
    * id  
    * type: One of [analysis,custom,default,reserved] - analysis has sub props, custom is custom props, default are basic info about the system, reserved are further info about the system  
    * analysis:
        * siteid  
        * sitename  
        * dbid  
        * id  
        * name  

    id of the property is compounded of O- site id - analysis id - number of property

    e.g.   

    {  
        "id": "O-xxxxxxxxxx-yyyyyyy-z",  
        "name": "Your fancy analysis",  
        "type": "analysis",  
        "analysis": {  
            "id": yyyyyyy,  
            "siteid": xxxxxxxxxx,  
            "sitename": "Your analysis' sitename",  
            "dbid": xxxxxxxxxx,  
            "name": "Your property's name"  
        }  
    }  

*   DatabaseNames
    * name  
    * id  

*   FixletProperties
    * name  
    * id  

*   Sitenames
    * name  
    * id  

Useful parameters:  

*   Text shorten/unshorten:  
    shortentext  
    unshorten  
    
*   Pagination:  
    &results=-1&startIndex=0 will give you all results  
    &results=100&startIndex=300 will give you 100 results starting at the 300th result  
    This script is hardcoded for all results in the build_parameters function.  

*   Columns:  
    &c= column/property name to include  
    &sort= column/property name  
    &dir= direction (asc or desc)  
    
    Example:  
    &sort=column1&sort=column2&sort=column3&dir=asc&dir=desc&dir=asc&c=column1&c=column3&c=column2&c=column4  
    Will present 4 columns in this order: column1, column3, column2, column4  
    Sorted on column1 ascending, column2 descending, column3 ascending, column 4 unsorted  
    
    *c=R-Computer Name is required or your query will fail*  

