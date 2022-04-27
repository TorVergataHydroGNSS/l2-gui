from tkinter import *
from tkinter import messagebox
from tkinter.ttk import *
from tkinter import filedialog
import os
import subprocess
import yaml
import time
import copy


def input_generator(parentFrame, procInput, row):
    f_lbl = Label(parentFrame, text=procInput['label'])
    f_lbl.grid(row=row, column=0, pady=10, padx=10)
    f_in = Entry(parentFrame, width=50)
    f_in.insert(0, procInput.get('last', ''))
    f_in.grid(row=row, column=1, pady=10, padx=10)
    if procInput['type'] == 'dir':
        f_fnd = Button(parentFrame, text="dir",
                       command=lambda: f_in.insert(0,os.path.normpath(filedialog.askdirectory())))
    elif procInput['type'] == 'file':
        f_fnd = Button(parentFrame, text="file", command=lambda: f_in.insert(0,
            os.path.normpath(filedialog.askopenfile().name)))
    else:
        f_fnd = Label(parentFrame, text=procInput.get('type'))
    f_fnd.grid(row=row, column=2, pady=10, padx=10)
    procInput['entry'] = f_in


SOIL = 'L2PP-SM'
FREEZE = 'L2PP-FT'
INUNDATION = 'L2PP-SI'
FOREST = 'L2PP-FB'

with open(os.path.join(os.getcwd(), 'settings.yaml'), 'r') as c:
    config: dict = yaml.load(c, yaml.SafeLoader)
    


# ROOT
window = Tk()
window.title("L2 Processors command/setup generator")
mainFrame = Frame(window)
mainFrame.grid(row=0, column=0)

# TABS
tabControl = Notebook(mainFrame)
tabControl.grid(row=0, column=0)

state: dict = copy.deepcopy(config)
for procName, procState in state.items():
    tabFrame = Frame(tabControl)
    tabFrame.grid()
    tabControl.add(tabFrame, text=procName)
    for row, procInput in enumerate(procState['inputs']):
        input_generator(tabFrame, procInput, row)


def generate_setup(inputRefs, setupTemplate):
    setupContent = setupTemplate
    for inputRef in inputRefs:
        setupContent = setupContent.replace(
            '{'+inputRef['id']+'}', inputRef['entry'].get())
    return setupContent


def generate_command(inputRefs, argsTemplate, execPath):
    commandArgs = argsTemplate
    for inputRef in inputRefs:
        commandArgs = commandArgs.replace(
            '{'+inputRef['id']+'}', inputRef['entry'].get())
    return execPath + ' ' + commandArgs


# RUN
def run():

    try:
        selectedProc = tabControl.tab(tabControl.select(), "text")

        # VALIDATE
        for inputRef in state[selectedProc]['inputs']:
            if not inputRef['entry'].get():
                raise Exception('All fields must be filled!')

        # LOCATE PROCESSOR
        execPath = os.path.normpath(filedialog.askopenfilename(
            title=f"Locate processor {selectedProc}"))
        execFolder = os.path.dirname(execPath)

        # PREPARE COMMAND / SETUP
        if not selectedProc == FREEZE:
            command = generate_command(
                state[selectedProc]['inputs'], state[selectedProc]['argsTemplate'], execPath)

        else:
            command = execPath
            setupContent = generate_setup(state[selectedProc]['inputs'],
                                          state[selectedProc]['setupTemplate'])
            with open(os.path.join(execFolder, 'Setupfile.txt'), 'w') as setupFile:
                setupFile.write(setupContent)

        # EXECUTE COMMAND
        completed = subprocess.run(
            ["powershell", "-Command", 'set-location', execFolder, ';', command], capture_output=True)

        # UPDATE LAST INPUTS
        for inputRef in state[selectedProc]['inputs']:
            configElement = next(item for item in config[selectedProc]['inputs'] if item["id"] == inputRef['id'])
            configElement['last'] = inputRef['entry'].get()
        
        with open(os.path.join(os.getcwd(), 'settings.yaml'), 'w') as c:
            yaml.safe_dump(config, c)

        # LOG SUCCESSFUL
        with open(os.path.join(os.getcwd(), f'log_{selectedProc}_{int(time.time())}.txt'), 'w') as log:
            log.write(
                f"---command---\n{command}\n---stdout---\n{str(completed.stdout)}\n---stderr---\n{str(completed.stderr)}\n---end---")

    except Exception as err:
        messagebox.showerror('Error', str(err))
        with open(os.path.join(os.getcwd(), f'log_{selectedProc}_{int(time.time())}_EXCEPTION.txt'), 'w') as log:
            log.write(f"---exception---\n{str(err)}\n---end---\n")

runBtn = Button(mainFrame, text='Select executable & launch', command=lambda: run())
runBtn.grid(column=0, row=1, sticky='WE')

window.mainloop()
