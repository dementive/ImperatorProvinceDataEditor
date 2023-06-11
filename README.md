# Imperator Rome Province Data Editor

The Imperator Rome Province Data Editor is a cross platform modern Python customtkinter application that is used to manage and edit all of the data in the province setup folder.

# Installation

Download the latest release of the repository and take the binary file out of the bin folder and put it where you want to use it.

# Setup

If you are setting the app up for the first time you will need to put a few files from your mod into the same directory as the app.

1. definition.csv - Your mod's province definition file

2. provincenames.yml - A file with all of the province names for your mod

3. provinces.png - Your mod's main province image file

4. Add the themes directory and all the files in it if you want to use some of the custom themes

In addition to these files you will also need to set all of the Application Settings that are listed below in the settings.json file to the correct values for your mod.

# How to Use

1. Complete all the setup, make sure all of your mod's data is added correctly.

2. Open the Application.

3. There is a zoom area with the provinces.png in it that can be zoomed into and moved around. There is also a frame on the side of the screen that has all the province data in it, here you can edit any data associated with the province and add new pops to the province.

4. Right-clicking any province on the province map will load all of it's information into the province data frame. When a province is right-clicked, if any province data has been changed, a save is triggered that will automatically rewrite all the data that was in the original file the province was found in. Note that right-clicking is currently the only way to trigger a save.

5. Exiting the application will automatically save all changes made to provinces names to output.

# Settings

There are several settings that allow you to change the appearance of the application.
All of the UI settings can be changed with a settings window that is opened with a button in the topbar.

UI settings
1. Theme

2. Color Scheme

3. UI Scaling

4. Layout

5. Menu Style

Application Settings
All of these need to be set to the correct values for the mod you are working on or the application will not function correctly as it will not have the data it needs.

1. Pop Types

2. Terrain Types

3. Cultures

4. Religions

5. Province Ranks

6. Trade Goods

![Screenshot](/assets/image1.png)

![Screenshot 2](/assets/image2.png)
