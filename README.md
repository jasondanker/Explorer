## Explorer ##
IO Lab Final Project, Fall 2016

*Team Members*:   
* Yiyi Chen
* Jason Danker
* Shrestha Mohanty
* Laura Montini
* Sasha Volkov  


## To Run ##
`sqlite3 app.db < schema.sql` (optional)  
`python run.py`  

## Input Suggestions ##
Amadeus API we use for travel search has some restrictions on what input values are accepted. below is an example search query that should give you some live result:   
Origin: San Francisco   
Departure Date: 2017-01-01  
Return Date: 2017-01-10  
Budget: 3000  
Destination: New York, New York  


## Release Notes (12/1) ##
* Updated front-end design to make the texts more eligible per feedback
* Implemented backend DB updates for trip, hotel and flights
* Connected to Amadeus and Google Maps API for hotel and flight search


## TODOs for Next Release (12/6) ##
* Update locations page to dynamically load a list of locations based on user input (now static value)
* Move DB write operations to the end of user trip creation
