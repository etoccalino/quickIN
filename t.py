import FreeSimpleGUI as sg


layout = [ [sg.Text('Hello, world!')] ]
window = sg.Window('Hello Example', layout)
while True:
    event, values = window.read()
    if event == sg.WIN_CLOSED:
        break

window.close()
