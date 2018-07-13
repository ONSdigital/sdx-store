# Helper scripts
 
## Export comments (export_comments.py)
### Description
This is used to get all the comments (q_code 146) from a survey for a given period.  It reads the comments and generates
an excel file with them in.
 
### Usage
 - Get the survey id and period that you wish to see the comments for
 - Run the script with ```python3 export_comments.py <survey_id> <period>``` (assuming you're in a virtual environment that has been set up correctly)
     - Example usage ```python3 export_comments.py 023 201807```