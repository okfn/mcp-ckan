# Engines?

This is an ongoing document to explore if we need engines and what for.  

This repo contains old and new version of mcp tool functions: https://github.com/okfn/mcp-bcie-portal/.  
We started with Python functions and you can easily realize that they are not scalable as is.  
IA propose engines which sound good and create a SQL and a YAML engines.  
They could be a good idea but we startted using them and the code is probably not simpler as we expected.  

## Next steps

They are some use cases that for sure are repetitive and can rely on a kind of engine. Some examples are:
 - A list of distict values for a column with filters (countries, years, etc): _Give me the list of countries with BCIE disbursements between 2010 and 2020_
 - A total amount with filters: _What is the total amount of BCIE disbursements to Honduras between 2015 and 2020?_
 - A list of records with filters: _Give me the list of BCIE disbursements to Honduras between 2015 and 2020 with details of year and amount_

So, if we forget about the engines: what'll be the best way to implement those use cases?  
Should we deploy a CSV to Pandas and or CSV to SQLite3 tools and define those use cases in python?  
Should we move back to pure Python?  
Are there more simpler engines that we can implement?  

I'm thinking on avoid generalizations and just be repetitive until the simplified code emerges.  
We can just cover simpler use cases.  
