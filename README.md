SMART PERSONAL FINANCE MANAGER
==============================

A fully offline desktop finance tracker built with Python, Tkinter, SQLite and Matplotlib.
The project files are transcribed from the uploaded 75-page build guide's complete-files appendix.

REQUIREMENTS
------------
- Python 3.10 or newer
- Tkinter (normally included with the standard Windows Python installer)
- matplotlib

WINDOWS SETUP
-------------
1. Create a folder 📂 for the proect.
2. Create the files.
3. Double-click run.bat, or open a terminal in this folder and run:

       py -m pip install -r requirements.txt
       py main.py

4. The first launch creates finance.db in this folder.

The application stores money as whole pesewa integers and keeps all records in the local
SQLite database. After Matplotlib is installed, the app works offline.

PROJECT FILES
-------------
main.py          Main window and tab controller
utils.py         Date and money helper functions
database.py      SQLite database operations
transactions.py  Add, edit, delete, search and filter transactions
sample_data.py   Optional example transactions and budgets
settings_tab.py  Currency, categories, backup and sample-data tools
budgets.py       Monthly category budgets
dashboard.py     Monthly overview and charts
reports.py       Date-range reports, CSV export and chart export

NOTES
-----
- The guide's sample-data loader is available in Settings.
- Use Settings > Backup to make a copy of your finance database.
- Do not delete finance.db unless you intend to remove your saved records.

ARTHUR
Adane Godfred Amofah
BSc. Computer Engineering
