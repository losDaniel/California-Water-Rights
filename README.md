# EWRIMS Scraped Database

This module scrapes the entire EWRIMS database including applications AND reports. Allows for appending new applications and reports to existing datasets. This module was developed in consultation with the Center for Environmental Economics and Sustainability Policy at the W.P. Carey School of Business under the direction of Dr. William Michael Hanemann. 

Applications: each application is an application to the water rights for a specific body of water. Applications may detail beneficial water use among other pertinant details. Applications may be submitted multiple times over time as required by local authorities, private contracts, or others. The state of California does not penalize a failure to apply for water rights so this database is not a complete representation of water use in the state.

Reports: reports may be submitted in association with particular applications. Reports cover a wide vireity of topics and may describe anything from the amount of water used over time to conservations efforts to changes to the project to methods of measurement.

There is an accompanying GIS component to this database that shows the bodies of water for california and allow for cross-referencing using latitude and longitude data in the application data. 

!(CaliforniaBodiesOfWater.PNG)

### ewrims_scrape.ipynb

This notebook provides a walkthrough of the methods in `ewmirs_scrape.py`. It will go step by step, applications and reports, comparing it to older data and appending new data into the database.

### Large Files

This repository uses [Git Large File Storage or LFS](https://git-lfs.github.com/) to store large files. 