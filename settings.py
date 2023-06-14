import json
from pathlib import Path
from PIL import Image


class Settings:
    def __init__(self):
        # Application Settings
        self.using_base_game_province_definitions = False
        self.path_to_base_game = ""
        self.path_to_mod = ""
        self.custom_maps = list()
        self.theme = ""
        self.color_scheme = ""
        self.ui_scaling = ""
        self.layout = ""
        self.menu_style = ""
        # Data Settings
        self.pop_types = list()
        self.terrain_types = list()
        self.cultures = list()
        self.religions = list()
        self.province_ranks = list()
        self.trade_goods = list()
        self.buildings = list()

    def write(self):
        # Write settings back to json file
        with open("settings.json", "w") as f:
            f.write("")
            f.write("{\n\t")
            base_game_path = self.path_to_base_game.replace("\\", "/")
            mod_path = self.path_to_mod.replace("\\", "/")
            f.write(f'"path_to_base_game": "{base_game_path}",\n\t')
            f.write(f'"path_to_mod": "{mod_path}",\n')
            self.write_json_list(f, "custom_maps", self.custom_maps)
            f.write(f'\t"theme": "{self.theme}",\n\t')
            f.write(f'"color_scheme": "{self.color_scheme}",\n\t')
            f.write(f'"ui_scaling": "{self.ui_scaling}",\n\t')
            f.write(f'"layout": "{self.layout}",\n\t')
            f.write(f'"menu_style": "{self.menu_style}",\n\t')
            f.write(
                f'"using_base_game_province_definitions": {str(self.using_base_game_province_definitions).lower()}\n'
            )
            f.write("}")

    def load(self):
        # Load settings from json file
        with open("settings.json", "r") as f:
            settings = json.load(f)

        # Application Settings
        self.using_base_game_province_definitions = settings["using_base_game_province_definitions"]
        self.path_to_base_game = settings["path_to_base_game"].replace("/", "\\")
        self.path_to_mod = settings["path_to_mod"].replace("/", "\\")
        custom_maps = list()
        for i in settings["custom_maps"]:
            path = Path(i)
            if path.is_dir():
                pillow_images = find_pillow_images_in_directory(path)
                for j in pillow_images:
                    full_path = j.resolve()
                    custom_maps.append(full_path)
            else:
                custom_maps.append(i)

        self.custom_maps = custom_maps
        self.theme = settings["theme"]
        self.layout = settings["layout"]
        self.color_scheme = settings["color_scheme"]
        self.menu_style = settings["menu_style"]
        self.ui_scaling = settings["ui_scaling"]

        if self.using_base_game_province_definitions:
            self.definition_csv = self.path_to_base_game + "\\map_data\\definition.csv"
        else:
            self.definition_csv = self.path_to_mod + "\\map_data\\definition.csv"

        if self.using_base_game_province_definitions:
            self.province_png = self.path_to_base_game + "\\map_data\\provinces.png"
        else:
            self.province_png = self.path_to_mod + "\\map_data\\provinces.png"

    def write_json_list(self, f, name, li, end=False):
        """
        Writes a list to a json file in a way that doens't look ugly, for some reason I couldn't find any other function to do this correctly
        """
        x = "" if end is True else ","
        f.write(f'\t"{name}": [')
        for i, j in enumerate(li):
            if i == len(li) - 1:
                f.write(f'"{j}"\n\t]{x}\n')
            elif i == 0:
                f.write(f'\n\t\t"{j}",\n\t\t')
            else:
                f.write(f'"{j}",\n\t\t')

    # These radio value functions are kind of stupid but it is super quick to implement new ones so I don't really want to rework it
    def get_theme_radio_value(self, value=None):
        if value:
            match value:
                case 1:
                    return "Dark"
                case 2:
                    return "Light"
                case 3:
                    return "System"
        else:
            match self.theme:
                case "Dark":
                    return 1
                case "Light":
                    return 2
                case "System":
                    return 3

    def get_scheme_radio_value(self, value=None):
        if value:
            match value:
                case 1:
                    return "blue"
                case 2:
                    return "dark-blue"
                case 3:
                    return "green"
                case 4:
                    return "themes/purple.json"
                case 5:
                    return "themes/gold.json"
                case 6:
                    return "themes/orange.json"
                case 7:
                    return "themes/red.json"
        else:
            match self.color_scheme:
                case "blue":
                    return 1
                case "dark-blue":
                    return 2
                case "green":
                    return 3
                case "themes/purple.json":
                    return 4
                case "themes/gold.json":
                    return 5
                case "themes/orange.json":
                    return 6
                case "themes/red.json":
                    return 7

    def get_ui_scaling_radio_value(self, value=None):
        if value:
            match value:
                case 1:
                    return "80%"
                case 2:
                    return "90%"
                case 3:
                    return "100%"
                case 4:
                    return "110%"
                case 5:
                    return "120%"
        else:
            match self.ui_scaling:
                case "80%":
                    return 1
                case "90%":
                    return 2
                case "100%":
                    return 3
                case "110%":
                    return 4
                case "120%":
                    return 5

    def get_layout_radio_value(self, value=None):
        if value:
            match value:
                case 1:
                    return "normal"
                case 2:
                    return "inverted"
        else:
            match self.layout:
                case "normal":
                    return 1
                case "inverted":
                    return 2

    def get_menu_style_radio_value(self, value=None):
        if value:
            match value:
                case 1:
                    return "titlebar"
                case 2:
                    return "menubar"
        else:
            match self.menu_style:
                case "titlebar":
                    return 1
                case "menubar":
                    return 2


def is_pillow_image(file_path):
    try:
        Image.open(file_path)
        return True
    except IOError:
        return False


def find_pillow_images_in_directory(directory):
    return [file_path for file_path in directory.iterdir() if is_pillow_image(file_path)]
