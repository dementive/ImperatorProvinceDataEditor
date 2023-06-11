import json


class Settings:
    def __init__(self):
        # Application Settings
        self.path_to_province_setup = ""
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
            f.write(f'"path_to_province_setup": "{self.path_to_province_setup}",\n\t')
            f.write(f'"theme": "{self.theme}",\n\t')
            f.write(f'"color_scheme": "{self.color_scheme}",\n\t')
            f.write(f'"ui_scaling": "{self.ui_scaling}",\n\t')
            f.write(f'"layout": "{self.layout}",\n\t')
            f.write(f'"menu_style": "{self.menu_style}",\n')
            self.write_json_list(f, "pop_types", self.pop_types)
            self.write_json_list(f, "terrain_types", self.terrain_types)
            self.write_json_list(f, "cultures", self.cultures)
            self.write_json_list(f, "religions", self.religions)
            self.write_json_list(f, "province_ranks", self.province_ranks)
            self.write_json_list(f, "trade_goods", self.trade_goods)
            self.write_json_list(f, "buildings", self.buildings, end=True)
            f.write("}")

    def load(self):
        # Load settings from json file
        with open("settings.json", "r") as f:
            settings = json.load(f)

        # Application Settings
        self.path_to_province_setup = settings["path_to_province_setup"]
        self.theme = settings["theme"]
        self.layout = settings["layout"]
        self.color_scheme = settings["color_scheme"]
        self.menu_style = settings["menu_style"]
        self.ui_scaling = settings["ui_scaling"]

        # Data Settings
        self.pop_types = settings["pop_types"]
        self.terrain_types = settings["terrain_types"]
        self.cultures = settings["cultures"]
        self.religions = settings["religions"]
        self.province_ranks = settings["province_ranks"]
        self.trade_goods = settings["trade_goods"]
        self.buildings = settings["buildings"]

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
