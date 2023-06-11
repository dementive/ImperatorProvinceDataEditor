import tkinter as tk
import customtkinter
import pandas as pd
import math
import re
import warnings
from platform import system
from pathlib import Path
from PIL import Image, ImageTk, ImageGrab
from settings import Settings
from CTkExtensions.CTkScrollableDropdown import *
from CTkExtensions.CTkToolTip import *
from CTkExtensions.CTkMenuBar import *

# Hardcoded settings
settings = Settings()
settings.load()
customtkinter.set_appearance_mode(settings.theme)
customtkinter.set_default_color_theme(settings.color_scheme)
customtkinter.set_widget_scaling(int(settings.ui_scaling.replace("%", "")) / 100)

# Global Variables
OS = system()
changed_provinces = set()
changed_provinces_data = dict()

# Non-GUI code


class ProvinceData:
    # All province data except for pops and buildings
    def __init__(self, data):
        self.province_id = ""
        self.province_name = ""
        self.terrain = ""
        self.culture = ""
        self.religion = ""
        self.trade_goods = ""
        self.province_rank = ""
        self.civilization_value = ""
        self.holy_site = ""

        attr_list = [
            "province_id",
            "province_name",
            "terrain",
            "culture",
            "religion",
            "trade_goods",
            "province_rank",
            "civilization_value",
            "holy_site",
        ]
        for attr, value in data:
            if attr in attr_list:
                setattr(self, attr, value)


def update_pop_tuple(pop_tuple):
    # Set default values for all tuples values for pops.
    keyword, current_values = pop_tuple
    keys = ["culture", "religion", "amount"]
    new_values = []

    for key in keys:
        value = next((v for k, v in current_values if k == key), "")
        new_values.append((key, value))

    return keyword, new_values


def get_province_output(province_data: dict):
    # Return the output for a province that will be written to a province setup file

    province = f'{province_data["province_id"]}={{ # {province_data["province_name"]}\n'
    province += f'\tterrain="{province_data["terrain"]}"\n'
    province += f'\tculture="{province_data["culture"]}"\n'
    province += f'\treligion="{province_data["religion"]}"\n'
    province += f'\ttrade_goods="{province_data["trade_good"]}"\n'
    province += f'\tcivilization_value={province_data["civ_value"]}\n'
    province += f"\tbarbarian_power=0\n"
    province += f'\tprovince_rank="{province_data["province_rank"]}"\n'

    # Pop format:
    # li = [
    #     ("citizen", [("culture", ""), ("religion", ""), ("amount", "3")]),
    #     ("freemen", [("culture", ""), ("religion", ""), ("amount", "3")]),
    #     ("slaves", [("culture", ""), ("religion", ""), ("amount", "3")]),
    # ]
    for i in province_data["pops"]:
        province += f"\t{i[0]}={{\n"
        if i[1][0][1] != "":
            province += f'\t\tculture="{i[1][0][1]}"\n'
        if i[1][1][1] != "":
            province += f'\t\treligion="{i[1][1][1]}"\n'
        province += f'\t\tamount="{i[1][2][1]}"\n'
        province += "\t}\n"

    holy_site = province_data["holy_site"]
    if holy_site:
        province += f'\tholy_site="{holy_site}"\n'

    # Building format:
    # li = [
    #     ("port_building", "3"),
    #     ("library_building", "2"),
    #     ("commerce_building", "2"),
    #     ("town_hall_building", "1"),
    #     ("aqueduct_building", "2"),
    # ]
    for i in province_data["buildings"]:
        province += f"\t{i[0]}={i[1]}\n"
    province += "}\n"

    return province


def get_pops_and_buildings(current_data):
    buildings = list()
    pops = list()
    for i, element in enumerate(current_data):
        if any(element[0].startswith(pop_type) for pop_type in settings.pop_types):
            pops.append(element)
        if element[0].endswith("_building"):
            buildings.append(element)

    pops = [update_pop_tuple(t) for t in pops]
    return pops, buildings


class ProvinceDefinition:
    def __init__(self, pid, r, g, b):
        self.id = pid
        self.rgb = (r, g, b)


def fix_definition_csv():
    # skip first 2 lines because they break pandas.read_csv
    first_id = ""
    with open("definition.csv") as file:
        next(file)
        next(file)
        content = []
        for i, line in enumerate(file):
            if i == 0:
                first_id = line
            content.append(line)

    with open("fixed_definition.csv", "w") as output_file:
        for line in content:
            output_file.write(line)

    return first_id


def load_definitions():
    first_id = fix_definition_csv()
    first_province = first_id.split(";")
    data = pd.read_csv("fixed_definition.csv", sep=";")
    df = pd.DataFrame(data)
    id_column = df.iloc[:, 0]
    r_column = df.iloc[:, 1]
    g_column = df.iloc[:, 2]
    b_column = df.iloc[:, 3]

    merged_list = zip(id_column, r_column, g_column, b_column)
    province_data = [i for i in merged_list]
    province_list = list()
    rgb_list = list()
    p = ProvinceDefinition(
        first_province[0],
        int(first_province[1]),
        int(first_province[2]),
        int(first_province[3]),
    )
    rgb_list.append(p.rgb)
    province_list.append(p)
    for i in province_data:
        p = ProvinceDefinition(i[0], i[1], i[2], i[3])
        province_list.append(p)
        rgb_list.append(p.rgb)

    return (province_list, rgb_list)


def match_nested_brackets(text, start=0):
    open_brackets = 0
    for i, char in enumerate(text[start:]):
        if char == "{":
            open_brackets += 1
        elif char == "}":
            open_brackets -= 1
            if open_brackets == 0:
                return start + i
    return None


def get_provinces_in_file(text):
    # Get the block of text for each province in a province setup file
    pattern = re.compile(r"\d+={", re.DOTALL)
    matches = pattern.finditer(text)
    provinces = list()

    for match in matches:
        start = match.start()
        end = match_nested_brackets(text, start + 1)
        if end is not None:
            provinces.append(text[start : end + 1])

    return provinces


def parse_province_data(text):
    match = re.search(r"\d+", text)
    if match:
        province_id = match.group()

    lines = text.split("\n")
    parsed_data = [("province_id", province_id)]

    for i in range(len(lines)):
        line = lines[i].strip()

        if any(line.startswith(pop_type) for pop_type in settings.pop_types):
            block_name = line.split("=")[0].strip()
            block_data = []
            i += 1
            line = lines[i].strip()

            while line != "}":
                key, value = line.split("=")
                block_data.append((key.strip(), value.strip().strip('"')))
                i += 1
                line = lines[i].strip()

            parsed_data.append((block_name, block_data))
        elif "=" in line and not line.startswith(province_id):
            key, value = line.split("=")
            if key == "amount":
                continue
            if (key == "religion" or key == "culture") and i > 6:
                continue
            parsed_data.append((key.strip(), value.strip().strip('"')))

    first_pop = ""
    for i, data in enumerate(parsed_data):
        if data[0] in settings.pop_types:
            first_pop = i

    pop_data_list = list()
    extra_data = list()

    if first_pop:
        for i in parsed_data[first_pop:]:
            if i[0] in settings.pop_types:
                pop_data_list.append(i)
            if i[0] in "holy_site" or re.search(r"_building$", i[0]):
                extra_data.append(i)
        return parsed_data[:first_pop] + pop_data_list + extra_data
    else:
        return parsed_data


def split_loc_key(string):
    string = string.strip()
    parts = string.split(":")
    key = parts[0]
    value = parts[1].replace('"', "").replace("\n", "").strip()
    return (key, value)


def get_province_names():
    # Get province names from yml settings file.
    # Supports links to other province name keys like - PROV2: $PROV1$
    province_names = dict()
    keys_with_links = list()
    with open("provincenames.yml", "r") as f:
        data = f.readlines()
    for i in data:
        if i.startswith("PROV"):
            if "$" in i:
                keys_with_links.append(i)
                continue
            i = i.split("PROV")
            province_data = split_loc_key(i[1])
            province_names[province_data[0]] = province_data[1]

    for i in keys_with_links:
        i = i.strip().replace('"', "").replace("$", "").replace("PROV", "").replace(" ", "")
        i = i.split(":")
        try:
            i[1] = province_names[i[1]]
        except KeyError:
            i[1] = f"EMPTY LOC - {i[0]}"
        province_names[i[0]] = i[1]

    return province_names


def save_all_changes():
    current_pid = application.province_data_frame.province_id
    current_province_name = application.province_data_frame.province_name
    current_culture = application.province_data_frame.culture.get()
    current_religion = application.province_data_frame.religion.get()
    current_trade_good = application.province_data_frame.trade_good.get()
    current_civ_value = application.province_data_frame.civ_value.get()
    current_province_rank = application.province_data_frame.province_rank.get()
    current_terrain = application.province_data_frame.terrain.get()
    current_holy_site = application.province_data_frame.holy_site.get()

    current_buildings = list()
    for i in application.province_data_frame.building_widgets:
        building_type = i.building_type
        building_count = i.building_count.get()
        if building_count and building_count > 0:
            current_buildings.append((building_type, str(building_count)))

    current_pops = list()
    for i in application.province_data_frame.pop_widgets:
        poptype = i.poptype.strip().lower()
        culture = i.popculture.strip().lower()
        religion = i.popreligion.strip().lower()
        amount = i.popcount.get()
        if amount and amount > 0:
            current_pops.append((poptype, [("culture", culture), ("religion", religion), ("amount", amount)]))

    current_province_data = {
        "province_id": current_pid.get(),
        "province_name": current_province_name.get(),
        "terrain": current_terrain,
        "culture": current_culture,
        "religion": current_religion,
        "trade_good": current_trade_good,
        "province_rank": current_province_rank,
        "civ_value": current_civ_value,
        "holy_site": current_holy_site,
        "buildings": current_buildings,
        "pops": current_pops,
    }

    changed_provinces_data[current_pid.get()] = current_province_data

    application.province_data_frame.province_names[current_pid.get()] = current_province_name.get()

    if current_pid.get() in changed_provinces:
        file_to_write = id_to_file_dict[current_pid.get()]
        provinces_to_write = [k for k, v in id_to_file_dict.items() if v == file_to_write]
        Path("output").mkdir(parents=True, exist_ok=True)
        # Write the file
        with open("output/" + file_to_write, "w") as file:
            for i in provinces_to_write:
                if i in changed_provinces:
                    province_data = changed_provinces_data[i]
                    file.write(get_province_output(province_data))
                else:
                    current_data = all_province_data[int(i) - 1]
                    pops, buildings = get_pops_and_buildings(current_data)
                    province_data = ProvinceData(current_data)
                    name = application.province_data_frame.province_names[province_data.province_id]
                    province_data = {
                        "province_id": province_data.province_id,
                        "province_name": name,
                        "terrain": province_data.terrain,
                        "culture": province_data.culture,
                        "religion": province_data.religion,
                        "trade_good": province_data.trade_goods,
                        "province_rank": province_data.province_rank,
                        "civ_value": province_data.civilization_value,
                        "holy_site": province_data.holy_site,
                        "buildings": buildings,
                        "pops": pops,
                    }
                    file.write(get_province_output(province_data))


# GUI code


def province_map_click_callback(event):
    global application, changed_provinces_data

    x, y = event.x_root, event.y_root
    image = ImageGrab.grab((x, y, x + 1, y + 1))
    color = image.getpixel((0, 0))

    province_id = 0
    if color not in province_definitions[1]:
        return

    idx = province_definitions[1].index(color)
    province_id = province_definitions[0][idx].id

    # Save all of the data from the current province into the main data frame
    save_all_changes()

    # Recreate the province data frame with the data from the clicked province

    if province_id in changed_provinces:
        new_province_data = changed_provinces_data[province_id]
    else:
        current_data = all_province_data[int(province_id) - 1]
        new_pops, new_buildings = get_pops_and_buildings(current_data)
        province_data = ProvinceData(current_data)

        new_province_data = {
            "province_id": province_data.province_id,
            "terrain": province_data.terrain,
            "culture": province_data.culture,
            "religion": province_data.religion,
            "trade_good": province_data.trade_goods,
            "province_rank": province_data.province_rank,
            "civilization_value": province_data.civilization_value,
            "holy_site": province_data.holy_site,
            "buildings": new_buildings,
            "pops": new_pops,
        }

    application.province_data_frame.startup_complete = False
    application.province_data_frame.province_id = tk.StringVar(value=new_province_data["province_id"])
    application.province_data_frame.set_province_id_to_name()
    application.province_data_frame.terrain = tk.StringVar(value=new_province_data["terrain"])
    application.province_data_frame.culture = tk.StringVar(value=new_province_data["culture"])
    application.province_data_frame.religion = tk.StringVar(value=new_province_data["religion"])
    application.province_data_frame.trade_good = tk.StringVar(value=new_province_data["trade_good"])
    application.province_data_frame.province_rank = tk.StringVar(value=new_province_data["province_rank"])

    if province_id in changed_provinces:
        application.province_data_frame.civ_value = tk.IntVar(value=int(new_province_data["civ_value"]))
    else:
        application.province_data_frame.civ_value = tk.IntVar(
            value=int(new_province_data["civilization_value"])
        )

    application.province_data_frame.holy_site = tk.StringVar(value=new_province_data["holy_site"])
    application.province_data_frame.buildings = new_province_data["buildings"]
    application.province_data_frame.pops = new_province_data["pops"]

    application.province_data_frame.province_name_entry.delete("0", tk.END)
    application.province_data_frame.province_name_entry.insert(
        -1, application.province_data_frame.province_name.get()
    )

    application.province_data_frame.terrain_box.set(application.province_data_frame.terrain.get())
    application.province_data_frame.culture_box.set(application.province_data_frame.culture.get())
    application.province_data_frame.religion_box.set(application.province_data_frame.religion.get())
    application.province_data_frame.trade_good_box.set(application.province_data_frame.trade_good.get())
    application.province_data_frame.province_rank_box.set(application.province_data_frame.province_rank.get())

    application.province_data_frame.civ_value_slider.set(application.province_data_frame.civ_value.get())
    application.province_data_frame.holy_site_entry.delete("0", tk.END)
    application.province_data_frame.holy_site_entry.insert(
        -1, application.province_data_frame.holy_site.get()
    )

    # Destroy the existing building widgets and recreate new ones
    for i in application.province_data_frame.building_widgets:
        i.destroy()

    application.province_data_frame.building_widgets = list()
    for i in application.province_data_frame.buildings:
        application.province_data_frame.create_building(i[0], i[1])

    # Destroy the existing pop widgets and recreate new ones
    for i in application.province_data_frame.pop_widgets:
        i.destroy()

    application.province_data_frame.pop_widgets = list()
    for i in application.province_data_frame.pops:
        application.province_data_frame.create_pop(i[0], i[1][2][1], i[1][0][1], i[1][1][1])

    application.province_data_frame.startup_complete = True


class AutoScrollbar(customtkinter.CTkScrollbar):
    """A scrollbar that hides itself if it's not needed. Works only for grid geometry manager"""

    def set(self, lo, hi):
        if float(lo) <= 0.0 and float(hi) >= 1.0:
            self.grid_remove()
        else:
            self.grid()
            customtkinter.CTkScrollbar.set(self, lo, hi)

    def pack(self, **kw):
        raise tk.TclError("Cannot use pack with the widget " + self.__class__.__name__)

    def place(self, **kw):
        raise tk.TclError("Cannot use place with the widget " + self.__class__.__name__)


class ZoomArea:
    """
    Display and zoom image
    Entirely based on https://github.com/foobar167/junkyard/blob/master/zoom_advanced3.py but updated to use customtkinter widgets
    """

    def __init__(self, placeholder, path):
        """Initialize the ImageFrame"""
        self.imscale = 1.0  # scale for the canvas image zoom, public for outer classes
        self.__delta = 1.3  # zoom magnitude
        self.__filter = Image.NEAREST  # could be: NEAREST, BILINEAR, BICUBIC and ANTIALIAS
        self.__previous_state = 0  # previous state of the keyboard
        self.path = path  # path to the image, should be public for outer classes
        # Create ImageFrame in placeholder widget
        self.__imframe = customtkinter.CTkFrame(placeholder)  # placeholder of the ImageFrame object
        # Vertical and horizontal scrollbars for canvas
        hbar = AutoScrollbar(self.__imframe, orientation="horizontal")
        vbar = AutoScrollbar(self.__imframe, orientation="vertical")
        hbar.grid(row=1, column=0, sticky="we")
        vbar.grid(row=0, column=1, sticky="ns")
        # Create canvas and bind it with scrollbars. Public for outer classes
        if customtkinter.get_appearance_mode() == "Dark":
            self.canvas = tk.Canvas(
                self.__imframe,
                highlightthickness=0,
                xscrollcommand=hbar.set,
                yscrollcommand=vbar.set,
                bg="#1a1a1a",
            )
        else:
            self.canvas = tk.Canvas(
                self.__imframe,
                highlightthickness=0,
                xscrollcommand=hbar.set,
                yscrollcommand=vbar.set,
            )
        self.canvas.grid(row=0, column=0, sticky="nswe")
        self.canvas.update()  # wait till canvas is created
        hbar.configure(command=self.__scroll_x)  # bind scrollbars to the canvas
        vbar.configure(command=self.__scroll_y)
        # Bind events to the Canvas
        self.canvas.bind("<Configure>", lambda event: self.__show_image())  # canvas is resized
        self.canvas.bind("<ButtonPress-1>", self.__move_from)  # remember canvas position
        self.canvas.bind("<B1-Motion>", self.__move_to)  # move canvas to the new position
        self.canvas.bind("<MouseWheel>", self.__wheel)  # zoom for Windows and MacOS, but not Linux
        self.canvas.bind("<Button-5>", self.__wheel)  # zoom for Linux, wheel scroll down
        self.canvas.bind("<Button-4>", self.__wheel)  # zoom for Linux, wheel scroll up
        # Handle keystrokes in idle mode, because program slows down on a weak computers,
        # when too many key stroke events in the same time
        self.canvas.bind("<Key>", lambda event: self.canvas.after_idle(self.__keystroke, event))
        # Decide if this image huge or not
        self.__huge = False  # huge or not
        self.__huge_size = 14000  # define size of the huge image
        self.__band_width = 1024  # width of the tile band
        Image.MAX_IMAGE_PIXELS = 1000000000  # suppress DecompressionBombError for big image
        with warnings.catch_warnings():  # suppress DecompressionBombWarning for big image
            warnings.simplefilter("ignore")
            self.__image = Image.open(self.path)  # open image, but down't load it into RAM
        self.imwidth, self.imheight = self.__image.size  # public for outer classes
        if (
            self.imwidth * self.imheight > self.__huge_size * self.__huge_size
            and self.__image.tile[0][0] == "raw"
        ):  # only raw images could be tiled
            self.__huge = True  # image is huge
            self.__offset = self.__image.tile[0][2]  # initial tile offset
            self.__tile = [
                self.__image.tile[0][0],  # it have to be 'raw'
                [0, 0, self.imwidth, 0],  # tile extent (a rectangle)
                self.__offset,
                self.__image.tile[0][3],
            ]  # list of arguments to the decoder
        self.__min_side = min(self.imwidth, self.imheight)  # get the smaller image side
        # Create image pyramid
        self.__pyramid = [self.smaller()] if self.__huge else [Image.open(self.path)]
        # Set ratio coefficient for image pyramid
        self.__ratio = max(self.imwidth, self.imheight) / self.__huge_size if self.__huge else 1.0
        self.__curr_img = 0  # current image from the pyramid
        self.__scale = self.imscale * self.__ratio  # image pyramide scale
        self.__reduction = 2  # reduction degree of image pyramid
        (w, h), m, j = self.__pyramid[-1].size, 512, 0
        n = math.ceil(math.log(min(w, h) / m, self.__reduction)) + 1  # image pyramid length
        while w > m and h > m:  # top pyramid image is around 512 pixels in size
            j += 1
            w /= self.__reduction  # divide on reduction degree
            h /= self.__reduction  # divide on reduction degree
            self.__pyramid.append(self.__pyramid[-1].resize((int(w), int(h)), self.__filter))
        # Put image into container rectangle and use it to set proper coordinates to the image
        self.container = self.canvas.create_rectangle((0, 0, self.imwidth, self.imheight), width=0)
        self.__show_image()  # show image on the canvas
        self.canvas.focus_set()  # set focus on the canvas
        self.canvas.bind("<Button-3>", province_map_click_callback)

    def smaller(self):
        """Resize image proportionally and return smaller image"""
        w1, h1 = float(self.imwidth), float(self.imheight)
        w2, h2 = float(self.__huge_size), float(self.__huge_size)
        aspect_ratio1 = w1 / h1
        aspect_ratio2 = w2 / h2  # it equals to 1.0
        if aspect_ratio1 == aspect_ratio2:
            image = Image.new("RGB", (int(w2), int(h2)))
            k = h2 / h1  # compression ratio
            w = int(w2)  # band length
        elif aspect_ratio1 > aspect_ratio2:
            image = Image.new("RGB", (int(w2), int(w2 / aspect_ratio1)))
            k = h2 / w1  # compression ratio
            w = int(w2)  # band length
        else:  # aspect_ratio1 < aspect_ration2
            image = Image.new("RGB", (int(h2 * aspect_ratio1), int(h2)))
            k = h2 / h1  # compression ratio
            w = int(h2 * aspect_ratio1)  # band length
        i, j, n = 0, 0, math.ceil(self.imheight / self.__band_width)
        while i < self.imheight:
            j += 1
            band = min(self.__band_width, self.imheight - i)  # width of the tile band
            self.__tile[1][3] = band  # set band width
            self.__tile[2] = self.__offset + self.imwidth * i * 3  # tile offset (3 bytes per pixel)
            self.__image.close()
            self.__image = Image.open(self.path)  # reopen / reset image
            self.__image.size = (self.imwidth, band)  # set size of the tile band
            self.__image.tile = [self.__tile]  # set tile
            cropped = self.__image.crop((0, 0, self.imwidth, band))  # crop tile band
            image.paste(cropped.resize((w, int(band * k) + 1), self.__filter), (0, int(i * k)))
            i += band
        return image

    def redraw_figures(self):
        """Dummy function to redraw figures in the children classes"""
        pass

    def grid(self, **kw):
        """Put ZoomArea widget on the parent widget"""
        self.__imframe.grid(**kw)  # place ZoomArea widget on the grid
        self.__imframe.grid(sticky="nswe")  # make frame container sticky
        self.__imframe.rowconfigure(0, weight=1)  # make canvas expandable
        self.__imframe.columnconfigure(0, weight=1)

    def pack(self, **kw):
        """Exception: cannot use pack with this widget"""
        raise Exception("Cannot use pack with the widget " + self.__class__.__name__)

    def place(self, **kw):
        """Exception: cannot use place with this widget"""
        raise Exception("Cannot use place with the widget " + self.__class__.__name__)

    # noinspection PyUnusedLocal
    def __scroll_x(self, *args, **kwargs):
        """Scroll canvas horizontally and redraw the image"""
        self.canvas.xview(*args)  # scroll horizontally
        self.__show_image()  # redraw the image

    # noinspection PyUnusedLocal
    def __scroll_y(self, *args, **kwargs):
        """Scroll canvas vertically and redraw the image"""
        self.canvas.yview(*args)  # scroll vertically
        self.__show_image()  # redraw the image

    def __show_image(self):
        """Show image on the Canvas. Implements correct image zoom almost like in Google Maps"""
        box_image = self.canvas.coords(self.container)  # get image area
        box_canvas = (
            self.canvas.canvasx(0),  # get visible area of the canvas
            self.canvas.canvasy(0),
            self.canvas.canvasx(self.canvas.winfo_width()),
            self.canvas.canvasy(self.canvas.winfo_height()),
        )
        box_img_int = tuple(map(int, box_image))  # convert to integer or it will not work properly
        # Get scroll region box
        box_scroll = [
            min(box_img_int[0], box_canvas[0]),
            min(box_img_int[1], box_canvas[1]),
            max(box_img_int[2], box_canvas[2]),
            max(box_img_int[3], box_canvas[3]),
        ]
        # Horizontal part of the image is in the visible area
        if box_scroll[0] == box_canvas[0] and box_scroll[2] == box_canvas[2]:
            box_scroll[0] = box_img_int[0]
            box_scroll[2] = box_img_int[2]
        # Vertical part of the image is in the visible area
        if box_scroll[1] == box_canvas[1] and box_scroll[3] == box_canvas[3]:
            box_scroll[1] = box_img_int[1]
            box_scroll[3] = box_img_int[3]
        # Convert scroll region to tuple and to integer
        self.canvas.configure(scrollregion=tuple(map(int, box_scroll)))  # set scroll region
        x1 = max(box_canvas[0] - box_image[0], 0)  # get coordinates (x1,y1,x2,y2) of the image tile
        y1 = max(box_canvas[1] - box_image[1], 0)
        x2 = min(box_canvas[2], box_image[2]) - box_image[0]
        y2 = min(box_canvas[3], box_image[3]) - box_image[1]
        if int(x2 - x1) > 0 and int(y2 - y1) > 0:  # show image if it in the visible area
            if self.__huge and self.__curr_img < 0:  # show huge image, which does not fit in RAM
                h = int((y2 - y1) / self.imscale)  # height of the tile band
                self.__tile[1][3] = h  # set the tile band height
                self.__tile[2] = self.__offset + self.imwidth * int(y1 / self.imscale) * 3
                self.__image.close()
                self.__image = Image.open(self.path)  # reopen / reset image
                self.__image.size = (self.imwidth, h)  # set size of the tile band
                self.__image.tile = [self.__tile]
                image = self.__image.crop((int(x1 / self.imscale), 0, int(x2 / self.imscale), h))
            else:  # show normal image
                image = self.__pyramid[max(0, self.__curr_img)].crop(  # crop current img from pyramid
                    (
                        int(x1 / self.__scale),
                        int(y1 / self.__scale),
                        int(x2 / self.__scale),
                        int(y2 / self.__scale),
                    )
                )
            #
            imagetk = ImageTk.PhotoImage(image.resize((int(x2 - x1), int(y2 - y1)), self.__filter))
            imageid = self.canvas.create_image(
                max(box_canvas[0], box_img_int[0]),
                max(box_canvas[1], box_img_int[1]),
                anchor="nw",
                image=imagetk,
            )
            self.canvas.lower(imageid)  # set image into background
            self.canvas.imagetk = imagetk  # keep an extra reference to prevent garbage-collection

    def __move_from(self, event):
        """Remember previous coordinates for scrolling with the mouse"""
        self.canvas.scan_mark(event.x, event.y)

    def __move_to(self, event):
        """Drag (move) canvas to the new position"""
        self.canvas.scan_dragto(event.x, event.y, gain=1)
        self.__show_image()  # zoom tile and show it on the canvas

    def outside(self, x, y):
        """Checks if the point (x,y) is outside the image area"""
        bbox = self.canvas.coords(self.container)  # get image area
        if bbox[0] < x < bbox[2] and bbox[1] < y < bbox[3]:
            return False  # point (x,y) is inside the image area
        else:
            return True  # point (x,y) is outside the image area

    def __wheel(self, event):
        """Zoom with mouse wheel"""
        x = self.canvas.canvasx(event.x)  # get coordinates of the event on the canvas
        y = self.canvas.canvasy(event.y)
        if self.outside(x, y):
            return  # zoom only inside image area
        scale = 1.0
        if OS == "Darwin":
            if event.delta < 0:  # scroll down, zoom out, smaller
                if round(self.__min_side * self.imscale) < 30:
                    return  # image is less than 30 pixels
                self.imscale /= self.__delta
                scale /= self.__delta
            if event.delta > 0:  # scroll up, zoom in, bigger
                i = float(min(self.canvas.winfo_width(), self.canvas.winfo_height()) >> 1)
                if i < self.imscale:
                    return  # 1 pixel is bigger than the visible area
                self.imscale *= self.__delta
                scale *= self.__delta
        else:
            # Respond to Linux (event.num) or Windows (event.delta) wheel event
            if event.num == 5 or event.delta == -120:  # scroll down, zoom out, smaller
                if round(self.__min_side * self.imscale) < 30:
                    return  # image is less than 30 pixels
                self.imscale /= self.__delta
                scale /= self.__delta
            if event.num == 4 or event.delta == 120:  # scroll up, zoom in, bigger
                i = float(min(self.canvas.winfo_width(), self.canvas.winfo_height()) >> 1)
                if i < self.imscale:
                    return  # 1 pixel is bigger than the visible area
                self.imscale *= self.__delta
                scale *= self.__delta
        # Take appropriate image from the pyramid
        k = self.imscale * self.__ratio  # temporary coefficient
        self.__curr_img = min((-1) * int(math.log(k, self.__reduction)), len(self.__pyramid) - 1)
        self.__scale = k * math.pow(self.__reduction, max(0, self.__curr_img))
        #
        self.canvas.scale("all", x, y, scale, scale)  # rescale all objects
        # Redraw some figures before showing image on the screen
        self.redraw_figures()  # method for child classes
        self.__show_image()

    def __keystroke(self, event):
        """Scrolling with the keyboard.
        Independent from the language of the keyboard, CapsLock, <Ctrl>+<key>, etc."""
        if event.state - self.__previous_state == 4:  # means that the Control key is pressed
            pass  # do nothing if Control key is pressed
        else:
            self.__previous_state = event.state  # remember the last keystroke state
            # Up, Down, Left, Right keystrokes
            if event.keycode in [68, 39, 102]:  # scroll right, keys 'd' or 'Right'
                self.__scroll_x("scroll", 1, "unit", event=event)
            elif event.keycode in [65, 37, 100]:  # scroll left, keys 'a' or 'Left'
                self.__scroll_x("scroll", -1, "unit", event=event)
            elif event.keycode in [87, 38, 104]:  # scroll up, keys 'w' or 'Up'
                self.__scroll_y("scroll", -1, "unit", event=event)
            elif event.keycode in [83, 40, 98]:  # scroll down, keys 's' or 'Down'
                self.__scroll_y("scroll", 1, "unit", event=event)

    def crop(self, bbox):
        """Crop rectangle from the image and return it"""
        if self.__huge:  # image is huge and not totally in RAM
            band = bbox[3] - bbox[1]  # width of the tile band
            self.__tile[1][3] = band  # set the tile height
            self.__tile[2] = self.__offset + self.imwidth * bbox[1] * 3  # set offset of the band
            self.__image.close()
            self.__image = Image.open(self.path)  # reopen / reset image
            self.__image.size = (self.imwidth, band)  # set size of the tile band
            self.__image.tile = [self.__tile]
            return self.__image.crop((bbox[0], 0, bbox[2], band))
        else:  # image is totally in RAM
            return self.__pyramid[0].crop(bbox)

    def destroy(self):
        """ImageFrame destructor"""
        self.__image.close()
        map(lambda i: i.close, self.__pyramid)  # close all pyramid images
        del self.__pyramid[:]  # delete pyramid list
        del self.__pyramid  # delete pyramid variable
        self.canvas.destroy()
        self.__imframe.destroy()


class ProvinceMap(tk.Frame):
    """Zoomable image class"""

    def __init__(self, mainframe, path):
        """Initialize the main Frame"""
        tk.Frame.__init__(self, master=mainframe)
        self.master.rowconfigure(0, weight=1)  # make the ZoomArea widget expandable
        self.master.columnconfigure(0, weight=1)
        canvas = ZoomArea(self.master, path)  # create widget
        canvas.grid(row=0, column=0)  # show widget


class BuildingFrame(customtkinter.CTkFrame):
    def __init__(self, master, name, amount, **kwargs):
        color = "#D3D3D3" if settings.theme == "Light" else "#1a1a1a"
        super().__init__(master, fg_color=color, **kwargs)

        self.building_type = name
        self.building_count = tk.IntVar(value=int(amount))

        self.remove_buildings_button = customtkinter.CTkButton(
            self, width=5, text="—", command=self.remove_buildings
        )
        self.remove_buildings_button.grid(row=0, column=0, padx=(150, 7), pady=(0, 0))
        if self.building_count.get() == 1:
            self.remove_buildings_button.configure(text="⨉")

        self.add_buildings_button = customtkinter.CTkButton(
            self, width=5, text="+", command=self.add_buildings
        )
        self.add_buildings_button.grid(row=0, column=0, padx=(7, 150), pady=(0, 0))

        self.building_type_label = customtkinter.CTkLabel(
            self,
            text=f"{self.building_type} - {self.building_count.get()}",
            font=customtkinter.CTkFont(size=12, weight="bold"),
            justify="center",
            anchor="w",
            wraplength=110,
        )
        self.building_type_label.grid(row=0, column=0, padx=(5, 15), pady=(3, 3))

        # Place frame on grid
        self.grid(row=0, column=3, padx=(0, 0), pady=(0, 0), sticky="w")
        self.grid_columnconfigure(0, weight=1)

        # Keybindings
        self.add_buildings_button.bind("<Button-3>", self.add_more_buildings)
        self.remove_buildings_button.bind("<Button-3>", self.remove_more_buildings)

    def update_label(self):
        self.building_type_label.configure(text=f"{self.building_type} - {self.building_count.get()}")

    def remove_buildings(self):
        self.building_count = tk.IntVar(value=self.building_count.get() - 1)
        self.update_label()
        if self.building_count.get() == 1:
            self.remove_buildings_button.configure(text="⨉")
        if self.building_count.get() <= 0:
            self.destroy()
        self.master.set_changed()

    def add_buildings(self):
        from_x = False
        if self.building_count.get() == 1:
            from_x = True
        self.building_count = tk.IntVar(value=self.building_count.get() + 1)
        self.update_label()
        if from_x:
            self.remove_buildings_button.configure(text="—")
        self.master.set_changed()

    def add_more_buildings(self, event):
        from_x = False
        if self.building_count.get() == 1:
            from_x = True
        self.building_count = tk.IntVar(value=self.building_count.get() + 3)
        self.update_label()
        if from_x:
            self.remove_buildings_button.configure(text="—")
        self.master.set_changed()

    def remove_more_buildings(self, event):
        self.building_count = tk.IntVar(value=self.building_count.get() - 3)
        self.update_label()
        if self.building_count.get() == 1:
            self.remove_buildings_button.configure(text="⨉")
        if self.building_count.get() <= 0:
            self.destroy()
        self.master.set_changed()


class PopFrame(customtkinter.CTkFrame):
    def __init__(self, master, popinfo, **kwargs):
        color = "#D3D3D3" if settings.theme == "Light" else "#1a1a1a"
        super().__init__(master, fg_color=color, **kwargs)

        self.poptype = popinfo[0]
        self.popcount = tk.IntVar(value=int(popinfo[1]))
        self.popculture = popinfo[2]
        self.popreligion = popinfo[3]

        if self.popculture:
            self.popculture = "\n" + self.popculture
        if self.popreligion:
            self.popreligion = "\n" + self.popreligion
        self.remove_pops_button = customtkinter.CTkButton(self, width=5, text="—", command=self.remove_pops)
        self.remove_pops_button.grid(row=0, column=0, padx=(150, 7), pady=(0, 0))
        if self.popcount.get() == 1:
            self.remove_pops_button.configure(text="⨉")

        self.add_pops_button = customtkinter.CTkButton(self, width=5, text="+", command=self.add_pops)
        self.add_pops_button.grid(row=0, column=0, padx=(7, 150), pady=(0, 0))

        self.poptype_label = customtkinter.CTkLabel(
            self,
            text=f"{self.poptype} - {self.popcount.get()}{self.popculture}{self.popreligion}",
            font=customtkinter.CTkFont(size=13, weight="bold"),
            justify="center",
            anchor="w",
            wraplength=110,
        )
        self.poptype_label.grid(row=0, column=0, padx=(5, 15), pady=(3, 3))

        # Place frame on grid
        self.grid(row=0, column=3, padx=(0, 0), pady=(0, 0), sticky="w")
        self.grid_columnconfigure(0, weight=1)

        # Keybindings
        self.add_pops_button.bind("<Button-3>", self.add_more_pops)
        self.remove_pops_button.bind("<Button-3>", self.remove_more_pops)

    def update_label(self):
        self.poptype_label.configure(
            text=f"{self.poptype} - {self.popcount.get()}{self.popculture}{self.popreligion}"
        )

    def remove_pops(self):
        self.popcount = tk.IntVar(value=self.popcount.get() - 1)
        self.update_label()
        if self.popcount.get() == 1:
            self.remove_pops_button.configure(text="⨉")
        if self.popcount.get() <= 0:
            self.destroy()
        self.master.set_changed()

    def add_pops(self):
        from_x = False
        if self.popcount.get() == 1:
            from_x = True
        self.popcount = tk.IntVar(value=self.popcount.get() + 1)
        self.update_label()
        if from_x:
            self.remove_pops_button.configure(text="—")
        self.master.set_changed()

    def add_more_pops(self, event):
        from_x = False
        if self.popcount.get() == 1:
            from_x = True
        self.popcount = tk.IntVar(value=self.popcount.get() + 5)
        self.update_label()
        if from_x:
            self.remove_pops_button.configure(text="—")
        self.master.set_changed()

    def remove_more_pops(self, event):
        self.popcount = tk.IntVar(value=self.popcount.get() - 5)
        self.update_label()
        if self.popcount.get() == 1:
            self.remove_pops_button.configure(text="⨉")
        if self.popcount.get() <= 0:
            self.destroy()
        self.master.set_changed()


class AddBuildingsFrame(customtkinter.CTkFrame):
    def __init__(self, master, **kwargs):
        color = "#D3D3D3" if settings.theme == "Light" else "#1a1a1a"
        super().__init__(master, fg_color=color, **kwargs)
        self.building_type = tk.StringVar(value="port_building")
        self.building_count = 1

        # Culture combobox
        self.building_combobox = customtkinter.CTkComboBox(
            self,
            width=160,
            values=settings.buildings,
            command=self.building_callback,
            variable=self.building_type,
        )
        self.building_combobox.grid(row=1, column=0, padx=(5, 5), pady=(10, 0))
        CTkToolTip(
            self.building_combobox,
            delay=0.5,
            message=f"Change building type",
            alpha=0.925,
            border_color="#DCE4EE",
            x_offset=-40,
        )
        CTkScrollableDropdown(
            self.building_combobox,
            command=self.building_dropdown_callback,
            values=settings.buildings,
            justify="left",
            button_color="transparent",
            autocomplete=True,
            resize=False,
            width=200,
            height=200,
            x=-16,
        )

        self.confirm_button = customtkinter.CTkButton(
            self,
            width=160,
            text="Confirm",
            command=self.confirm_callback,
            fg_color="transparent",
            border_width=2,
            text_color=("gray10", "#DCE4EE"),
        )
        self.confirm_button.grid(row=2, column=0, padx=(4, 0), pady=(10, 5))
        self.tooltip_2 = CTkToolTip(
            self.confirm_button,
            delay=0.5,
            message=f"Add {self.building_count} {self.building_type.get()} buildings",
            alpha=0.925,
            border_color="#DCE4EE",
            x_offset=-105,
        )

    def update_tooltip(self):
        self.tooltip_2.configure(
            message=f"Add {self.building_count} {self.building_type.get()}",
        )

    def confirm_callback(self):
        self.master.create_building(self.building_type.get(), self.building_count)

    def building_callback(self, event):
        self.building_type = tk.StringVar(value=self.building_combobox.get())
        self.update_tooltip()

    def building_dropdown_callback(self, choice):
        self.building_type = tk.StringVar(value=choice)
        self.building_combobox.set(self.building_type.get())
        self.update_tooltip()


class AddPopsFrame(customtkinter.CTkFrame):
    def __init__(self, master, **kwargs):
        color = "#D3D3D3" if settings.theme == "Light" else "#1a1a1a"
        super().__init__(master, fg_color=color, **kwargs)

        self.culture_list = [""] + settings.cultures
        self.religion_list = [""] + settings.religions
        self.pop_type_list = settings.pop_types

        self.radio_var = tk.IntVar(value=1)
        self.pop_count = tk.IntVar(value=1)
        self.pop_count_out = 1
        self.pop_type = "Nobles"
        self.pop_culture = tk.StringVar(value="")
        self.pop_religion = tk.StringVar(value="")
        self.tooltip_1 = ""
        self.tooltip_2 = ""

        # Pop type radio buttons
        for i, pop in enumerate(self.pop_type_list):
            radio = customtkinter.CTkRadioButton(
                self,
                text=pop,
                command=self.poptype_callback,
                variable=self.radio_var,
                value=i + 1,
            )
            radio.grid(row=i, column=0, padx=(0, 65), pady=(3, 3))
            CTkToolTip(
                radio,
                delay=0.5,
                message=f"Add {pop} pops.",
                alpha=0.925,
                border_color="#DCE4EE",
                x_offset=0,
            )

        # Pop count slider
        self.pop_count_slider_one = customtkinter.CTkSlider(
            self,
            from_=0,
            to=25,
            command=self.update_slider,
            width=177,
            variable=self.pop_count,
        )
        self.pop_count_slider_one.grid(row=len(self.pop_type_list) - 1, column=0, padx=(88, 0), pady=(4, 0))
        self.tooltip_1 = CTkToolTip(
            self.pop_count_slider_one,
            delay=0.5,
            message=str(self.pop_count.get()),
            alpha=0.925,
            border_color="#DCE4EE",
            x_offset=0,
        )

        # Culture combobox
        self.culture = customtkinter.CTkComboBox(
            self,
            width=85,
            values=self.culture_list,
            command=self.culture_callback,
            variable=self.pop_culture,
        )
        self.culture.grid(row=len(self.pop_type_list), column=0, padx=(0, 88), pady=(4, 0))
        CTkToolTip(
            self.culture,
            delay=0.5,
            message=f"Set culture.",
            alpha=0.925,
            border_color="#DCE4EE",
            x_offset=-40,
        )
        CTkScrollableDropdown(
            self.culture,
            command=self.culture_dropdown_callback,
            values=self.culture_list,
            justify="left",
            button_color="transparent",
            autocomplete=True,
            resize=False,
            width=200,
            height=200,
            x=-16,
            y=-203,
        )

        # Religion combobox
        self.religion = customtkinter.CTkComboBox(
            self,
            width=85,
            values=self.culture_list,
            command=self.religion_callback,
            variable=self.pop_religion,
        )
        self.religion.grid(row=len(self.pop_type_list), column=0, padx=(88, 0), pady=(4, 0))
        CTkToolTip(
            self.religion,
            delay=0.5,
            message=f"Set religion.",
            alpha=0.925,
            border_color="#DCE4EE",
            x_offset=-40,
        )
        CTkScrollableDropdown(
            self.religion,
            command=self.religion_dropdown_callback,
            values=self.religion_list,
            justify="left",
            button_color="transparent",
            autocomplete=True,
            resize=False,
            width=200,
            height=200,
            x=-104,
            y=-203,
        )

        self.confirm_button = customtkinter.CTkButton(
            self,
            width=180,
            text="Confirm",
            command=self.confirm_callback,
            fg_color="transparent",
            border_width=2,
            text_color=("gray10", "#DCE4EE"),
        )
        self.confirm_button.grid(row=len(self.pop_type_list) + 1, column=0, padx=(4, 0), pady=(15, 0))
        self.tooltip_2 = CTkToolTip(
            self.confirm_button,
            delay=0.5,
            message=f"Add {self.pop_count_out} {self.pop_culture.get()} {self.pop_type} pops",
            alpha=0.925,
            border_color="#DCE4EE",
            x_offset=-105,
            y_offset=-50,
        )

        # Place frame on grid
        self.grid(row=0, column=3, padx=(0, 0), pady=(0, 0), sticky="w")
        self.grid_columnconfigure(0, weight=1)

        self.culture.bind("<Return>", command=self.culture_callback)
        self.religion.bind("<Return>", command=self.religion_callback)

    def update_tooltip(self):
        rel = self.pop_religion.get() + " "
        self.tooltip_2.configure(
            message=f"Add {self.pop_count.get()} {self.pop_culture.get()} {rel}{self.pop_type} pops"
        )

    def confirm_callback(self):
        self.master.create_pop(
            self.pop_type,
            self.pop_count.get(),
            self.pop_culture.get(),
            self.pop_religion.get(),
        )

    def poptype_callback(self):
        self.pop_type = self.pop_type_list[self.radio_var.get() - 1]
        self.update_tooltip()

    def culture_callback(self, event):
        self.pop_culture = tk.StringVar(value=self.culture.get())
        self.update_tooltip()

    def culture_dropdown_callback(self, choice):
        self.pop_culture = tk.StringVar(value=choice)
        self.culture.set(self.pop_culture.get())
        self.update_tooltip()

    def religion_callback(self, event):
        self.pop_religion = tk.StringVar(value=self.religion.get())
        self.update_tooltip()

    def religion_dropdown_callback(self, choice):
        self.pop_religion = tk.StringVar(value=choice)
        self.religion.set(self.pop_religion.get())
        self.update_tooltip()

    def update_slider(self, value):
        self.pop_count = tk.IntVar(value=int(self.pop_count_slider_one.get()))
        self.tooltip_1.configure(message=str(int(value)))
        self.pop_count_out = int(value)
        self.update_tooltip()


class ProvinceDataFrame(customtkinter.CTkScrollableFrame):
    def __init__(self, master, province_data: dict, **kwargs):
        super().__init__(master, **kwargs)
        content_x = (60, 0)
        label_fontsize = 14
        header_fontsize = 18
        self.startup_complete = False
        self.pop_widgets = list()
        self.building_widgets = list()

        self.province_id = tk.StringVar(value=province_data["province_id"])
        self.terrain = tk.StringVar(value=province_data["terrain"])
        self.culture = tk.StringVar(value=province_data["culture"])
        self.religion = tk.StringVar(value=province_data["religion"])
        self.trade_good = tk.StringVar(value=province_data["trade_good"])
        self.province_rank = tk.StringVar(value=province_data["province_rank"])
        self.holy_site = tk.StringVar(value=province_data["holy_site"])
        self.pops = province_data["pops"]
        self.buildings = province_data["buildings"]
        # Slider values need to be IntVar
        self.civ_value = tk.IntVar(value=province_data["civilization_value"])

        self.current_open_buildings_row = 15
        self.current_open_pops_row = 101

        # Load province names localization
        self.province_names = get_province_names()

        upper_box_width = 135

        # Province name editbox
        self.province_name_entry_label = customtkinter.CTkLabel(
            self,
            text="Name",
            justify="center",
            font=customtkinter.CTkFont(size=label_fontsize, weight="bold"),
        )
        self.province_name_entry = customtkinter.CTkEntry(
            self, placeholder_text="1", width=upper_box_width, justify="left"
        )
        if OS != "Windows" or settings.menu_style == "menubar":
            # Move down when there is no titlebar
            self.province_name_entry_label.grid(row=1, column=0, padx=(0, 143), pady=(15, 0))
            self.province_name_entry.grid(row=1, column=0, padx=content_x, pady=(15, 0))
        else:
            self.province_name_entry_label.grid(row=1, column=0, padx=(0, 143), pady=(10, 0))
            self.province_name_entry.grid(row=1, column=0, padx=content_x, pady=(10, 0))

        self.set_province_id_to_name()
        self.province_name_entry.configure(textvariable=self.province_name)

        # Terrain combobox
        self.terrain_box = customtkinter.CTkComboBox(
            self,
            width=upper_box_width,
            values=settings.terrain_types,
            command=self.terrain_callback,
            variable=self.terrain,
        )
        self.terrain_box.grid(row=4, column=0, padx=content_x, pady=(20, 0))
        CTkScrollableDropdown(
            self.terrain_box,
            values=settings.terrain_types,
            justify="left",
            button_color="transparent",
            autocomplete=True,
            resize=False,
            width=200,
            height=375,
            x=-63,
        )
        self.terrain_box.set(self.terrain.get())
        self.terrain_label = customtkinter.CTkLabel(
            self,
            text="Terrain",
            font=customtkinter.CTkFont(size=label_fontsize, weight="bold"),
        )
        self.terrain_label.grid(row=4, column=0, padx=(0, 143), pady=(20, 0))

        # Culture combobox
        self.culture_box = customtkinter.CTkComboBox(
            self,
            width=upper_box_width,
            values=settings.cultures,
            command=self.culture_callback,
            variable=self.culture,
        )
        self.culture_box.grid(row=5, column=0, padx=content_x, pady=(20, 0))
        CTkScrollableDropdown(
            self.culture_box,
            command=self.culture_dropdown_callback,
            values=settings.cultures,
            justify="left",
            button_color="transparent",
            autocomplete=True,
            resize=False,
            width=200,
            height=375,
            x=-63,
        )
        self.culture_box.set(self.culture.get())
        self.culture_label = customtkinter.CTkLabel(
            self,
            text="Culture",
            font=customtkinter.CTkFont(size=label_fontsize, weight="bold"),
        )
        self.culture_label.grid(row=5, column=0, padx=(0, 143), pady=(20, 0))

        # Religion combobox
        self.religion_box = customtkinter.CTkComboBox(
            self,
            width=upper_box_width,
            values=settings.religions,
            command=self.religion_callback,
            variable=self.religion,
        )
        self.religion_box.grid(row=6, column=0, padx=content_x, pady=(20, 0))
        CTkScrollableDropdown(
            self.religion_box,
            command=self.religion_dropdown_callback,
            values=settings.religions,
            justify="left",
            button_color="transparent",
            autocomplete=True,
            resize=False,
            width=200,
            height=375,
            x=-63,
        )
        self.religion_box.set(self.religion.get())
        self.religion_label = customtkinter.CTkLabel(
            self,
            text="Religion",
            font=customtkinter.CTkFont(size=label_fontsize, weight="bold"),
        )
        self.religion_label.grid(row=6, column=0, padx=(0, 143), pady=(20, 0))

        # Trade Goods combobox
        self.trade_good_box = customtkinter.CTkComboBox(
            self,
            width=upper_box_width,
            values=settings.trade_goods,
            command=self.trade_good_callback,
            variable=self.trade_good,
        )
        self.trade_good_box.grid(row=7, column=0, padx=content_x, pady=(20, 0))
        CTkScrollableDropdown(
            self.trade_good_box,
            command=self.trade_good_dropdown_callback,
            values=settings.trade_goods,
            justify="left",
            button_color="transparent",
            autocomplete=True,
            resize=False,
            width=200,
            height=375,
            x=-63,
        )
        self.trade_good_box.set(self.trade_good.get())
        self.trade_good_label = customtkinter.CTkLabel(
            self,
            text="Goods",
            font=customtkinter.CTkFont(size=label_fontsize, weight="bold"),
        )
        self.trade_good_label.grid(row=7, column=0, padx=(0, 143), pady=(20, 0))

        # Province Rank option menu
        self.province_rank_box = customtkinter.CTkOptionMenu(
            self, width=upper_box_width, values=settings.province_ranks, variable=self.province_rank
        )
        self.province_rank_box.grid(row=8, column=0, padx=content_x, pady=(20, 0))
        CTkScrollableDropdown(
            self.province_rank_box,
            command=self.province_rank_dropdown_callback,
            values=settings.province_ranks,
            justify="left",
            button_color="transparent",
            scrollbar=False,
            resize=False,
            width=200,
            height=120,
            x=-63,
        )
        self.province_rank_box.set(self.province_rank.get())
        self.province_rank_label = customtkinter.CTkLabel(
            self,
            text="Rank",
            font=customtkinter.CTkFont(size=label_fontsize, weight="bold"),
        )
        self.province_rank_label.grid(row=8, column=0, padx=(0, 143), pady=(20, 0))

        # Holy site editbox
        self.holy_site_entry_label = customtkinter.CTkLabel(
            self,
            text="Holy Site",
            wraplength=50,
            font=customtkinter.CTkFont(size=14, weight="bold"),
        )
        self.holy_site_entry_label.grid(row=9, column=0, padx=(0, 145), pady=(20, 0))
        self.holy_site_entry = customtkinter.CTkEntry(
            self,
            placeholder_text="1",
            textvariable=self.holy_site,
            width=upper_box_width,
            justify="left",
        )
        self.holy_site_entry.grid(row=9, column=0, padx=content_x, pady=(20, 0))

        # Civ value slider
        self.civ_value_label = customtkinter.CTkLabel(
            self,
            text=f"Civilization Value: {self.civ_value.get()}",
            font=customtkinter.CTkFont(size=header_fontsize, weight="bold"),
        )
        self.civ_value_label.grid(row=10, column=0, padx=(0, 0), pady=(20, 0))
        self.civ_value_slider = customtkinter.CTkSlider(
            self,
            variable=self.civ_value,
            from_=0,
            to=100,
            command=self.update_civ_value,
        )
        self.civ_value_slider.grid(row=11, column=0, padx=(4, 0), pady=(4, 0))

        # Building widgets
        self.buildings_label = customtkinter.CTkLabel(
            self,
            text="Buildings",
            font=customtkinter.CTkFont(size=header_fontsize, weight="bold"),
        )
        self.buildings_label.grid(row=13, column=0, padx=(0, 0), pady=(10, 5))
        for i in self.buildings:
            self.create_building(i[0], i[1])

        # Create add buildings frame
        self.add_pops_frame = AddBuildingsFrame(self)
        # This is placed on row 99, which is right before the first population widget.
        self.add_pops_frame.grid(row=99, column=0, padx=(12, 9), pady=(4, 0))

        # Population widgets

        # Pops look like this when they get here:
        # [
        #     ("citizen", [("culture", "hebrew"), ("religion", "judaism"), ("amount", "4")]),
        #     ("nobles", [("culture", ""), ("religion", ""), ("amount", "5")]),
        #     ("citizen", [("culture", ""), ("religion", ""), ("amount", "20")]),
        #     ("freemen", [("culture", ""), ("religion", ""), ("amount", "21")]),
        #     ("slaves", [("culture", ""), ("religion", ""), ("amount", "4")]),
        #     ("tribesmen", [("culture", ""), ("religion", ""), ("amount", "4")]),
        # ]

        self.pops_label = customtkinter.CTkLabel(
            self,
            text="Population",
            font=customtkinter.CTkFont(size=header_fontsize, weight="bold"),
        )
        self.pops_label.grid(row=100, column=0, padx=(0, 0), pady=(10, 5))

        for i in self.pops:
            self.create_pop(i[0], i[1][2][1], i[1][0][1], i[1][1][1])

        # Create add pops frame
        self.add_pops_frame = AddPopsFrame(self)
        self.add_pops_frame.grid(
            row=500, column=0, padx=(12, 9), pady=(4, 0)
        )  # Row is a big number so pop frames can be added

        # Place frame on grid
        if settings.layout == "inverted":
            self.grid(row=0, column=0, padx=(20, 0), pady=(10, 0), sticky="nsew")
        else:
            self.grid(row=0, column=2, padx=(20, 0), pady=(10, 0), sticky="nsew")
        self.grid_columnconfigure(0, weight=1)

        # Keybindings
        self.province_name_entry.bind("<Return>", self.update_pid)
        self.holy_site_entry.bind("<Return>", self.holy_site_callback)
        self.culture_box.bind("<Return>", self.culture_callback)
        self.religion_box.bind("<Return>", self.religion_callback)
        self.trade_good_box.bind("<Return>", self.trade_good_callback)

        self.startup_complete = True

    # Callback functions
    def update_pid(self, event):
        self.province_name = tk.StringVar(value=self.province_name_entry.get())
        self.set_changed()

    def terrain_callback(self, event):
        self.terrain = tk.StringVar(value=self.terrain_box.get())
        self.set_changed()

    def terrain_dropdown_callback(self, choice):
        self.terrain = tk.StringVar(value=choice)
        self.terrain_box.set(self.terrain.get())
        self.set_changed()

    def culture_callback(self, event):
        self.culture = tk.StringVar(value=self.culture_box.get())
        self.set_changed()

    def culture_dropdown_callback(self, choice):
        self.culture = tk.StringVar(value=choice)
        self.culture_box.set(self.culture.get())
        self.set_changed()

    def religion_callback(self, event):
        self.religion = tk.StringVar(value=self.religion_box.get())
        self.set_changed()

    def religion_dropdown_callback(self, choice):
        self.religion = tk.StringVar(value=choice)
        self.religion_box.set(self.religion.get())
        self.set_changed()

    def trade_good_callback(self, event):
        self.trade_good = tk.StringVar(value=self.trade_good_box.get())
        self.set_changed()

    def trade_good_dropdown_callback(self, choice):
        self.trade_good = tk.StringVar(value=choice)
        self.trade_good_box.set(self.trade_good.get())
        self.set_changed()

    def province_rank_dropdown_callback(self, choice):
        self.province_rank = tk.StringVar(value=choice)
        self.province_rank_box.set(self.province_rank.get())
        self.set_changed()

    def update_civ_value(self, event):
        self.civ_value = tk.IntVar(value=int(self.civ_value_slider.get()))
        self.civ_value_label.configure(text=f"Civilization Value: {self.civ_value.get()}")
        self.set_changed()

    def holy_site_callback(self):
        self.holy_site = tk.StringVar(value=self.holy_site_entry.get())
        self.set_changed()

    # Helper Functions

    def set_changed(self):
        # Run on every callback function.
        # This indicates that something has changed with this province and it needs to be written in the output seperate from the parsed in data
        global changed_provinces
        if self.startup_complete is True and self.province_id.get() not in changed_provinces:
            changed_provinces.add(self.province_id.get())

    def set_province_id_to_name(self):
        try:
            self.province_name = tk.StringVar(value=self.province_names[self.province_id.get()])
        except KeyError:
            self.province_name = tk.StringVar(value=f"EMPTY LOC - {self.province_id.get()}")
        self.province_name_entry.delete("0", tk.END)
        self.province_name_entry.insert(-1, self.province_name.get())

    def create_pop(self, poptype, popcount, popculture, popreligion):
        # Create a new pop frame
        self.current_open_pops_row += 1
        new_pop = PopFrame(self, popinfo=(poptype.title(), popcount, popculture.title(), popreligion))
        new_pop.grid(row=self.current_open_pops_row, column=0, padx=(12, 9), pady=(4, 0))
        self.pop_widgets.append(new_pop)
        self.set_changed()

    def create_building(self, name, amount):
        # Create a new pop frame
        self.current_open_buildings_row += 1
        new_building = BuildingFrame(self, name, amount)
        new_building.grid(row=self.current_open_buildings_row, column=0, padx=(12, 9), pady=(4, 0))
        self.building_widgets.append(new_building)
        self.set_changed()


class SettingsWindow(customtkinter.CTkToplevel):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self.theme_var = tk.IntVar(value=settings.get_theme_radio_value())
        self.scheme_var = tk.IntVar(value=settings.get_scheme_radio_value())
        self.ui_scaling_var = tk.IntVar(value=settings.get_ui_scaling_radio_value())
        self.layout_var = tk.IntVar(value=settings.get_layout_radio_value())
        self.menu_style_var = tk.IntVar(value=settings.get_menu_style_radio_value())

        self.output_values = [
            settings.get_theme_radio_value(),
            settings.get_scheme_radio_value(),
            settings.get_ui_scaling_radio_value(),
            settings.get_layout_radio_value(),
            settings.get_menu_style_radio_value(),
        ]

        self.title("Settings")
        self.geometry("750x325")

        # Configure the grid
        self.rowconfigure(0, weight=1)
        self.rowconfigure(1, weight=0)
        self.columnconfigure(0, weight=1)
        self.columnconfigure(1, weight=1)
        self.columnconfigure(2, weight=1)
        self.columnconfigure(3, weight=1)
        self.columnconfigure(4, weight=1)

        # Make frames
        first_frame = customtkinter.CTkFrame(self)
        second_frame = customtkinter.CTkFrame(self)
        third_frame = customtkinter.CTkFrame(self)
        fourth_frame = customtkinter.CTkFrame(self)
        fifth_frame = customtkinter.CTkFrame(self)

        first_frame.grid(column=0, row=0, padx=(15, 10), pady=(15, 10), sticky="nsew")
        second_frame.grid(column=1, row=0, padx=5, pady=(15, 10), sticky="nsew")
        third_frame.grid(column=2, row=0, padx=5, pady=(15, 10), sticky="nsew")
        fourth_frame.grid(column=3, row=0, padx=5, pady=(15, 10), sticky="nsew")
        fifth_frame.grid(column=4, row=0, padx=(10, 15), pady=(15, 10), sticky="nsew")

        # Theme Setting
        self.theme_label = customtkinter.CTkLabel(
            first_frame,
            text="Theme",
            font=customtkinter.CTkFont(size=16, weight="bold", underline=True),
        )
        self.theme_label.pack(pady=2)
        theme_radio1 = customtkinter.CTkRadioButton(
            first_frame,
            text="Dark",
            command=self.theme_callback,
            variable=self.theme_var,
            value=1,
        )
        theme_radio1.pack(pady=5)
        theme_radio2 = customtkinter.CTkRadioButton(
            first_frame,
            text="Light",
            command=self.theme_callback,
            variable=self.theme_var,
            value=2,
        )
        theme_radio2.pack(pady=5)
        theme_radio3 = customtkinter.CTkRadioButton(
            first_frame,
            text="System",
            command=self.theme_callback,
            variable=self.theme_var,
            value=3,
        )
        theme_radio3.pack(pady=5)

        # Color Scheme Setting
        self.color_scheme_label = customtkinter.CTkLabel(
            second_frame,
            text="Color Scheme",
            font=customtkinter.CTkFont(size=16, weight="bold", underline=True),
        )
        self.color_scheme_label.pack(pady=2)
        scheme_radio1 = customtkinter.CTkRadioButton(
            second_frame,
            text="Blue",
            command=self.scheme_callback,
            variable=self.scheme_var,
            value=1,
        )
        scheme_radio1.pack(pady=5)

        scheme_radio2 = customtkinter.CTkRadioButton(
            second_frame,
            text="Dark-Blue",
            command=self.scheme_callback,
            variable=self.scheme_var,
            value=2,
        )
        scheme_radio2.pack(pady=5)

        scheme_radio3 = customtkinter.CTkRadioButton(
            second_frame,
            text="Green",
            command=self.scheme_callback,
            variable=self.scheme_var,
            value=3,
        )
        scheme_radio3.pack(pady=5)

        scheme_radio4 = customtkinter.CTkRadioButton(
            second_frame,
            text="Purple",
            command=self.scheme_callback,
            variable=self.scheme_var,
            value=4,
        )
        scheme_radio4.pack(pady=5)

        scheme_radio5 = customtkinter.CTkRadioButton(
            second_frame,
            text="Gold",
            command=self.scheme_callback,
            variable=self.scheme_var,
            value=5,
        )
        scheme_radio5.pack(pady=5)

        scheme_radio6 = customtkinter.CTkRadioButton(
            second_frame,
            text="Orange",
            command=self.scheme_callback,
            variable=self.scheme_var,
            value=6,
        )
        scheme_radio6.pack(pady=5)

        scheme_radio7 = customtkinter.CTkRadioButton(
            second_frame,
            text="Red",
            command=self.scheme_callback,
            variable=self.scheme_var,
            value=7,
        )
        scheme_radio7.pack(pady=5)

        # UI Scaling Setting
        self.ui_scaling_label = customtkinter.CTkLabel(
            third_frame,
            text="UI Scaling",
            font=customtkinter.CTkFont(size=16, weight="bold", underline=True),
        )
        self.ui_scaling_label.pack(pady=2)

        ui_scaling_radio1 = customtkinter.CTkRadioButton(
            third_frame,
            text="80%",
            command=self.ui_scaling_callback,
            variable=self.ui_scaling_var,
            value=1,
        )
        ui_scaling_radio1.pack(pady=5)

        ui_scaling_radio2 = customtkinter.CTkRadioButton(
            third_frame,
            text="90%",
            command=self.ui_scaling_callback,
            variable=self.ui_scaling_var,
            value=2,
        )
        ui_scaling_radio2.pack(pady=5)

        ui_scaling_radio3 = customtkinter.CTkRadioButton(
            third_frame,
            text="100%",
            command=self.ui_scaling_callback,
            variable=self.ui_scaling_var,
            value=3,
        )
        ui_scaling_radio3.pack(pady=5)

        ui_scaling_radio4 = customtkinter.CTkRadioButton(
            third_frame,
            text="110%",
            command=self.ui_scaling_callback,
            variable=self.ui_scaling_var,
            value=4,
        )
        ui_scaling_radio4.pack(pady=5)

        ui_scaling_radio5 = customtkinter.CTkRadioButton(
            third_frame,
            text="120%",
            command=self.ui_scaling_callback,
            variable=self.ui_scaling_var,
            value=5,
        )
        ui_scaling_radio5.pack(pady=5)

        # Layout Setting
        self.layout_label = customtkinter.CTkLabel(
            fourth_frame,
            text="Layout",
            font=customtkinter.CTkFont(size=16, weight="bold", underline=True),
        )
        self.layout_label.pack(pady=2)
        layout_radio1 = customtkinter.CTkRadioButton(
            fourth_frame,
            text="Normal",
            command=self.layout_callback,
            variable=self.layout_var,
            value=1,
        )
        layout_radio1.pack(pady=5)

        layout_radio2 = customtkinter.CTkRadioButton(
            fourth_frame,
            text="Inverted",
            command=self.layout_callback,
            variable=self.layout_var,
            value=2,
        )
        layout_radio2.pack(pady=5)

        # Menu Style Setting
        self.menu_style_label = customtkinter.CTkLabel(
            fifth_frame,
            text="Menu Style",
            font=customtkinter.CTkFont(size=16, weight="bold", underline=True),
        )
        self.menu_style_label.pack(pady=2)
        menu_style_radio1 = customtkinter.CTkRadioButton(
            fifth_frame,
            text="Title Bar",
            command=self.menu_style_callback,
            variable=self.menu_style_var,
            value=1,
        )
        menu_style_radio1.pack(pady=5)

        menu_style_radio2 = customtkinter.CTkRadioButton(
            fifth_frame,
            text="Menu Bar",
            command=self.menu_style_callback,
            variable=self.menu_style_var,
            value=2,
        )
        menu_style_radio2.pack(pady=5)

        # Confirmation button
        self.confirm_button = customtkinter.CTkButton(
            self,
            width=180,
            text="Confirm",
            command=self.confirm_callback,
            fg_color="transparent",
            border_width=2,
            text_color=("gray10", "#DCE4EE"),
        )
        self.confirm_button.grid(column=0, row=1, columnspan=5, sticky="ew", padx=300, pady=(5, 10))
        self.tooltip_2 = CTkToolTip(
            self.confirm_button,
            delay=0.5,
            message=f"Confirm changes made to settings. Settings will not apply until the application is restarted.",
            alpha=0.925,
            border_color="#DCE4EE",
        )

    # Callback Functions
    def theme_callback(self):
        self.output_values[0] = self.theme_var.get()

    def scheme_callback(self):
        self.output_values[1] = self.scheme_var.get()

    def ui_scaling_callback(self):
        self.output_values[2] = self.ui_scaling_var.get()

    def layout_callback(self):
        self.output_values[3] = self.layout_var.get()

    def menu_style_callback(self):
        self.output_values[4] = self.menu_style_var.get()

    def confirm_callback(self):
        settings.theme = settings.get_theme_radio_value(self.output_values[0])
        settings.color_scheme = settings.get_scheme_radio_value(self.output_values[1])
        settings.ui_scaling = settings.get_ui_scaling_radio_value(self.output_values[2])
        settings.layout = settings.get_layout_radio_value(self.output_values[3])
        settings.menu_style = settings.get_menu_style_radio_value(self.output_values[4])
        settings.write()
        self.destroy()


class App(customtkinter.CTk):
    def __init__(self):
        super().__init__()

        # Configure window
        self.title("Imperator Province Data Editor")
        self.geometry(f"{1700}x{880}")

        # Configure grid layout
        self.grid_columnconfigure(1, weight=1)
        self.grid_columnconfigure((2, 3, 4), weight=0)
        self.grid_rowconfigure((0, 1, 2), weight=1)

        # Create province data frame
        current_data = all_province_data[0]
        pops, buildings = get_pops_and_buildings(current_data)
        province_data = ProvinceData(current_data)

        default_province_data = {
            "province_id": province_data.province_id,
            "terrain": province_data.terrain,
            "culture": province_data.culture,
            "religion": province_data.religion,
            "trade_good": province_data.trade_goods,
            "province_rank": province_data.province_rank,
            "civilization_value": province_data.civilization_value,
            "holy_site": province_data.holy_site,
            "buildings": buildings,
            "pops": pops,
        }
        self.province_data_frame = ProvinceDataFrame(self, default_province_data, height=1000)

        # Create province map
        self.province_frame = customtkinter.CTkFrame(self, height=1000)
        ProvinceMap(self.province_frame, path="provinces.png")
        self.province_frame.grid(row=0, column=1, padx=(20, 0), pady=(10, 0), sticky="nsew")
        self.grid_propagate(False)

        # Create menu
        if OS == "Windows" and settings.menu_style == "titlebar":
            self.menu = CTkTitleMenu(self, x_offset=self.winfo_width() + 10)
        else:
            self.menu = CTkMenuBar(self)

        button_1 = self.menu.add_cascade("Settings")

        self.settings = None
        self.dropdown = CustomDropdownMenu(widget=button_1)
        self.dropdown.add_option(
            option="Open Settings",
            command=lambda: self.open_settings(),
        )

    def open_settings(self):
        if self.settings is None or not self.settings.winfo_exists():
            self.settings = SettingsWindow(self)
        else:
            self.settings.focus()

    def on_close(self):
        # Save all the changes made to provinces and localization
        # application.destroy() has to execute to close the app so we just except everything here to ensure it happens so you don't get stuck in the app if there is an error.

        loc_keys = list()
        try:
            save_all_changes()
        except Exception as e:
            print(e)
        try:
            for i, province in enumerate(application.province_data_frame.province_names):
                loc_key = ""
                if province not in changed_provinces:
                    loc_key = f"PROV{i+1}: " + f'"{application.province_data_frame.province_names[province]}"'
                else:
                    for item in changed_provinces:
                        if int(item) == i + 1:
                            loc_key = f"PROV{i+1}: " + f'"{changed_provinces_data[item]["province_name"]}"'
                if loc_key:
                    loc_keys.append(loc_key)
            Path("output").mkdir(parents=True, exist_ok=True)
            # Write the file
            with open("output/" + "provincenames_l_english.yml", "w") as file:
                file.write("l_english:\n")
                for i in loc_keys:
                    file.write(f" {i}\n")
        except Exception as e:
            print(e)

        application.destroy()


if __name__ == "__main__":
    global all_province_data, application

    # Parse all province setup data
    path_to_setup = Path(settings.path_to_province_setup)

    if not path_to_setup.is_dir():
        error = "The path to province setup defined in settings.json is not a valid directory!"
        raise NotADirectoryError(error)

    all_province_data = list()
    id_to_file_dict = dict()

    try:
        for filename in path_to_setup.iterdir():
            with open(filename, "r", encoding="utf-8-sig") as file:
                text = file.read()
            data = get_provinces_in_file(text)
            for i in data:
                parsed_data = parse_province_data(i)
                all_province_data.append(parsed_data)
                id_to_file_dict[parsed_data[0][1]] = filename.name
    except:
        error = (
            "There was an error parsing the province setup files."
            + "Make sure the path to the province setup directory is correct and there are no additional files in the province setup folder."
        )
        raise RuntimeError(error)

    # Load province definitions
    try:
        province_definitions = load_definitions()
    except:
        error = "There was an error loading province definitions. Make sure the definition.csv is formatted in the same way as the base game."
        raise RuntimeError(error)

    # Sort data by province ID
    all_province_data = sorted(all_province_data, key=lambda x: int(x[0][1]))

    application = App()
    application.after(0, lambda: application.state("zoomed"))
    application.protocol("WM_DELETE_WINDOW", application.on_close)
    application.mainloop()
