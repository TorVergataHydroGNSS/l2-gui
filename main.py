from tkinter import *
from tkinter import messagebox
from tkinter.ttk import *
from tkinter import filedialog
import re
import os
import pyperclip

def input_generator(parentFrame, row, name, type='file'):
    def fill_entry(entry):
        path = ''
        if type == 'file':
            path = filedialog.askopenfile().name
        elif type == 'dir':
            path = filedialog.askdirectory()
        else:
            raise Exception('Requested type error')
        entry.insert(0, os.path.normpath(path))

    f_lbl = Label(parentFrame, text=name)
    f_lbl.grid(row=row, column=0, pady=10, padx=10)
    f_in = Entry(parentFrame, width=50)
    f_in.grid(row=row, column=1, pady=10, padx=10)
    if type in ['file', 'dir']:
        f_fnd = Button(parentFrame, text=f"{type[0].upper()}{type[1:]}", command=lambda: fill_entry(f_in))
    else:
        f_fnd = Label(parentFrame, text=f"{type[0].upper()}{type[1:]}")
    f_fnd.grid(row=row, column=2, pady=10, padx=10)
    return f_in


SOIL = 'L2PP-SM'
FREEZE = 'L2PP-FT'
INUNDATION = 'L2PP-SI'
FOREST = 'L2PP-FB'

# PROCESSORS

p = {
    SOIL: {
        'frame': None,
        'interface': [
            ('InputDirectory', 'dir'),
            ('OutputDirectory', 'dir'),
            ('AuxiliaryDataDirectory', 'dir'),
            ('year', 'number'),
            ('month', 'number'),
            ('day', 'number'),
            ('NumberOfDay', 'number'),
            ('resolution', 'number'),
            ('signal', 'string'),
            ('polarization', 'string')
        ],
        'commandTemplate': 'SML2PP_start.exe -input %s %s %s %s %s %s %s %s %s %s',
        'fields': []
    },
    INUNDATION: {
        'frame': None,
        'interface': [
            ('DDMs File Path', 'file'),
            ('Metadata L1/L1b File Path', 'file'),
            ('Result File Path', 'dir'),
        ],
        'commandTemplate': 'L2_PSR.exe -D %s -M %s -R %s',
        'fields': []
    },
    FOREST: {
        'frame': None,
        'interface': [
            ('Selected date', 'date'),
            ('Root path', 'dir'),
        ],
        'commandTemplate': 'L2PP_FB.exe %s %s',
        'fields': []

    },
    FREEZE: {
        'frame': None,
        'interface': [
            ('commandsaga', 'dir'),
            ('paths.L1b', 'dir'),
            ('paths.L2FT', 'dir'),
            ('paths.Auxiliary', 'dir'),
            ('files.LandCover', 'file'),
            ('files.L1bfile', 'file'),
            ('startdate', 'datenum'),
            ('enddate', 'datenum')
        ],
        'commandTemplate': 'L2OPFT_mainscript.exe',
        'fields': [],
        'setupFileTemplate': '''
% This is setup file to define paths and variables for 
% L2OP FT module

% Common paths required for gdal and saga 

commandgdal = 'C:\"Program Files (x86)"\GDAL\'; % GDAL directory for GDAL command 
envirogdal = 'C:\Program Files (x86)\GDAL\gdal-data'; % GDAL enviromental varaible path
commandsaga = 'C:\Program Files (x86)\SAGA-GIS'; % OK

% Follwing will be needed later for operational processor to download latest snow extent data
% sidadscoloradoedu = 'ftp://sidads.colorado.edu/DATASETS/NOAA/G02156/GIS/4km/';
% wwwnaticenoaa = 'https://www.natice.noaa.gov/pub/ims/ims_v3/imstif/4km/';

paths.L1b = 'D:\HydroGNSS\L2\PDGS_NAS_folders\DataRelease\L1A_L1B';
paths.L2FT = 'D:\HydroGNSS\L2\PDGS_NAS_folders\DataRelease\L2OP-FT';
paths.Auxiliary = 'D:\HydroGNSS\L2\PDGS_NAS_folders\Auxiliary_Data';

files.LandCover = 'CCI_LC_2018_EASE2_300m.sg-grd';

% This is for testing purposes
files.L1bfile = 'metadata_L1_merged.nc';

startdate = datenum(2018,08,18);
enddate = datenum(2018,08,18);

% Parameters
% Footprint radius in meters
buf_r = '5000';
% Minimum latitude to be included
minlat = 45;
% maximum open water fraction allowed (LC210)
maxwater = 0.1;
% maximum incidence angle allowed
maxincangle = 40;
'''
    },
}

# ROOT
window = Tk()
window.title("L2 Processors command/setup generator")
mainFrame = Frame(window)
mainFrame.grid(row=0, column=0)

# TABS
tabControl = Notebook(mainFrame)
tabControl.grid(row=0, column=0)

for processor, configs in p.items():
    configs['frame'] = Frame(tabControl)
    configs['frame'].grid()
    tabControl.add(configs['frame'], text=processor)
    for i, input_desc in enumerate(configs['interface']):
        configs['fields'].append(input_generator(
            configs['frame'], i, input_desc[0], input_desc[1]))


# RUN
def run():
    selectedProc = tabControl.tab(tabControl.select(), "text")
    inputs = [field.get() for field in p[selectedProc]['fields']]

    # VALIDATE
    if len(p[selectedProc]['interface']) != len([field for field in inputs if field]):
        messagebox.showerror('Error', 'All fields must be filled!')
        return
    
    # POPUP
    toplevel = Toplevel()
    toplevelFrame = Frame(toplevel)
    toplevelFrame.grid()

    # GENERATE
    try:
        if(not selectedProc == FREEZE):
            command = p[selectedProc]['commandTemplate'] % tuple(inputs)
            action = lambda: pyperclip.copy(command)
            action_lbl = "Copy to Clipboard" 
            label = Label(toplevelFrame, text=command)
            label.grid(row=0, column=0, padx=20, pady=20)
        else:
            setup = p[selectedProc]['setupFileTemplate']
            def write():              
                with open(os.path.join(filedialog.askdirectory(), 'Setupfile.txt'), 'w') as output:
                    output.write(setup)
            action = lambda: write()
            action_lbl = 'Generate Setup File'
            for i,field in enumerate(inputs):
                regex = fr"{p[selectedProc]['interface'][i][0]}.*$"
                subst = f"{p[selectedProc]['interface'][i][0]} = '{field}'"
                setup = re.sub(regex, subst, setup, 1,re.MULTILINE)
    except Exception as e:
        messagebox.showerror('Error', str(e))
        return
        
    button_action = Button(toplevelFrame, text=action_lbl, command=action)
    button_action.grid(row=1, column=0, sticky='WE')
    button_close = Button(toplevelFrame, text="Close", command=toplevel.destroy)
    button_close.grid(row=2, column=0, sticky='WE')
    

runBtn = Button(mainFrame, text='Generate', command=lambda: run())
runBtn.grid(column=0, row=1, sticky='WE')

window.mainloop()
