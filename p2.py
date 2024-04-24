import FreeSimpleGUI as sg

def publish_to_trello(full_text):
    print(f'{full_text=}')


def build_window():
    sg.theme("DarkBlue3")
    sg.set_options(font=("Courier New", 16))

    layout = [[sg.Text('Reminder: first line is title, next lines become description')],
              [sg.Input(key='in', do_not_clear=False, focus=True)],
              [sg.Button('IN'), sg.Button('Clear')]]
    window = sg.Window('Quick to IN', layout, finalize=True)
    window['in'].bind('<Return>', '_Return')
    return window


def main():
    window = build_window()

    while True:
        
        match window.read():

            case (sg.WIN_CLOSED, _):
                break
            case ('Clear', _):
                print('Clear the text field')
                print(window['in'])
                window['in'].set_focus()
            case (event, values) if (
                    (event in ('in_Return', 'IN')) and
                    (values.get('in') is not None)):
                publish_to_trello(values['in'])
                window['in'].set_focus()
            case event, values:
                print(f'WAT. {event=} and {values=}')
                window['in'].set_focus()

    window.close()


if __name__ == '__main__':
    main()
