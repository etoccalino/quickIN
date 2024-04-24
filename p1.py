import FreeSimpleGUI as sg


def publish_to_trello(full_text):
    print(f'{full_text=}')


def build_window():
    layout = [[sg.Text('Reminder: first line is title, next lines become description')],
              [sg.InputText(key='in', do_not_clear=False, focus=True)],
              [sg.Button('IN'), sg.Button('Clear')]]
    window = sg.Window('Quick to IN', layout)
    return window


def main():
    window = build_window()

    while True:
        event, values = window.read()

        if event == sg.WIN_CLOSED:
            break
        elif event == 'Clear':
            print('Clear the text field')
            print(window['in'])
            window['in'].set_focus()
            continue

        if values.get('in') is None:
            raise RuntimeError(f'wat. {values=}')

        publish_to_trello(values['in'])
        window['in'].set_focus()

    window.close()


if __name__ == '__main__':
    main()
