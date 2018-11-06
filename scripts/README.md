# Helper scripts
 
## Export comments (export_comments.py)
### Description
This is used to get all the comments (q_code 146) from a survey for a given period.  It reads the comments and generates
an excel file with them in.
 
### Usage
 - Get the survey id and period that you wish to see the comments for
 - Run the script with ```python3 export_comments.py <survey_id> <period>``` (assuming you're in a virtual environment that has been set up correctly)
     - Example usage ```python3 export_comments.py 023 201807```
    
       
     
## Reset Invalid Store Data (reset_invalid_store_data.py)
### Description
This is used to remove the 'invalid' key from the stored data and set the store's invalid column to False so that the response can be reprocessed. 
The 'invalid' key is added by sdx-collect to identify invalid responses and was previously stored along with the response data.
This 'invalid' key in the stored data prohibits the reprocessing of the response and so in future will not be stored however for older responses it needs to be removed.
 
### Usage
 - Get the tx_ids for each response that you need to reset and put one per line within the file tx_ids.
 - Run the script with ```python3 reset_invalid_store_data.py``` (assuming you're in a virtual environment that has been set up correctly)
