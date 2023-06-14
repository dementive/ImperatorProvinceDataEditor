# Imperator Rome Province Data Editor

The Imperator Rome Province Data Editor is a cross platform modern Python customtkinter application that is used to manage and edit all of the data in the province setup folder.

# Installation

1. Download the repository.

2. Make a folder in your mod named `Province Data Editor`

3. Copy the contents of the `bin` folder into the new folder.

4. If your mod does not change the provinces.png or definition.csv set the `using_base_game_province_definitions` setting to `true`.

# Setup

If you are setting the app up for the first time you will need to change a few files.

1. settings.json - The application settings, two paths need to be set here for the app to work correctly. The path to the game and the path to your mod.

2. provincenames.yml - A file with all of the province names for your mod. Copy the exact structure of the existing file and fill it with your data.

# Features

1. There is a zoom area with the provinces.png in it that can be zoomed into and moved around, ctrl+mousewheel will double the speed of the zoom.

2. There is also a frame on the side of the screen that has all the province data in it, here you can edit any data associated with the province and add new pops to the province.

3. Right-clicking any province on the province map will load all of it's information into the province data frame. When a province is right-clicked, if any province data has been changed, a save is triggered that will automatically rewrite all the data that was in the original file the province was found in.

4. Alt/Ctrl/Shift-clicking on a province will show a tooltip that displays it's ID and name.

5. The main map canvas can be changed to use custom maps defined in settings or loaded at runtime in the Map Modes menu. Clicking on the menu button to load a new map mode will add it to the main canvas, right-clicking will load it into a canvas in a new window.

6. There is a simple search function that will let you set the current province data to a specific province ID.

7. Exiting the application or switching between provinces will automatically save all changes.

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

All of these need to be set to the correct values or the application will not function correctly as it will not have the data it needs.

1. path_to_base_game - This should be the path to the Imperator Rome game folder. If you do not want to load any data from the base game set this to an empty string.

2. path_to_mod - This should be the path to your mod.

3. custom_maps - This is a list of paths to files or directories that have custom maps to load into the program. All entries in this list will automatically get a button to be opened in the map modes menu. Custom maps can be any image. I recommend using the following GUI command in game to quickly run all the console commands needed to print the needed maps:
```
onclick = "[ExecuteConsoleCommandsForced('printmap political;printmap culture;printmap religion;printmap simple_terrain;printmap population;printmap fortifications;printmap civilization')]"
```

![Screenshot](/assets/image1.png)

![Screenshot 2](/assets/image2.png)

![Screenshot 4](/assets/image4.png)

![Screenshot 3](/assets/image3.png)

