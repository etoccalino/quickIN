import logging
import webbrowser

import FreeSimpleGUI as sg
import trello
import tomlkit
from requests.exceptions import HTTPError


class Config:
    '''TOML config, with filesystem validation and write-back.'''

    log = logging.getLogger('quickIN.config')

    def __init__(self, path):
        self.path = path
        self._toml = None
        self._load()

    def _load(self):
        '''Reloads the config from the config file.'''
        self.log.info(f'loading config from {self.path}')
        with open(self.path, 'r') as fp:
            self._toml = tomlkit.load(fp)
        self.log.debug(f'config loaded: {self._toml}')

    def update(self, section='', key='', value=''):
        '''Update a single (pre-existent) config value and persist immediately.'''
        self._toml[section][key] = value
        self.log.debug('persisting config')
        with open(self.path, 'w') as fp:
            tomlkit.dump(self._toml, fp)

    def get(self, key, default=None):
        return self._toml.get(key, default)

    def __getitem__(self, key):
        return self._toml[key]

    def __str__(self):
        return str(self._toml)


class Trello:
    '''Wrap Trello operations.'''

    log = logging.getLogger('quickIN.trello')

    def __init__(self, config):
        self._config = config
        self._trello = self._set_up_trello_client()

    def _set_up_trello_client(self):
        token = self._config.get('authorization', {}).get('token')
        client = trello.TrelloApi(self._config['authentication']['key'])
        client.set_token(token)
        return client

    def _retry_after_renewing_token(self, network_call_to_trello, *args, **kwargs):
        '''Wrap an instance method to retry network errors due to expired tokens.

        This function cannot be a wrapper because the recovery behavior
        `self._refresh_token()` requires the instance.
        '''
        retry_network_call = False

        try:
            return network_call_to_trello(*args, **kwargs)
        except HTTPError as http:
            if http.response is not None and http.response.status_code == 401:
                self.log.warning('Got a 401 response. Renewing the auth token...')
                self._refresh_token()
                self.log.info('Token renewed.')
                retry_network_call = True
        else:
            self.log.error('Got a "requests" error. Either a connection, network, or auth error')
            self.log.error(http)
            self.log.info('Review the config file for errors (e.g.: key, token)')
            raise

        if retry_network_call:
            self.log.info('Retrying with new token...')
            try:
                return network_call_to_trello(*args, **kwargs)
            except HTTPError as http:
                self.log.error('Another error. Bailing out...')
                raise

    def post_new_card(self, title, description=None):
        '''Creates a new card in Trello.

        Raises `requests.exceptions.HTTPError` if it fails to recover (once) from it.
        '''
        list_id = self._find_list_id()
        self.log.info('Sending new card to Trello')
        self._retry_after_renewing_token(
            self._trello.lists.new_card, list_id, title, None, description)
        self.log.info('New card created.')

    def _refresh_token(self):
        '''Prompt user for a new token and update the config and Trello client.'''
        token = self._prompt_user_for_token()
        self._config.update(section='authorization', key='token', value=token)
        self._trello.set_token(token)

    def _prompt_user_for_token(self):
        app = self._config['authentication']['app_name']
        url = self._trello.get_token_url(self._config['authentication']['app_name'],
                                         expires=self._config['authorization']['expiration'],
                                         write_access=True)
        self.log.info(f'Will now attempt to renew the authorization token for "{app}".')
        self.log.debug(f'Opening a browser to {url}')
        webbrowser.open(url)
        token = input(f'Please authorize "{app}" and copy-paste the token here: ')
        self.log.debug(f'got {token=}')
        return token

    def _find_list_id(self):
        '''Return the list ID.

        Loads the list ID from the config file. If not present, it'll try to fetch it from
        Trello and update the config.


        Raises `requests.exceptions.HTTPError` if it fails to recover (once) from it.
        '''
        # If present in the cofig, return it immediately
        if list_id := self._config.get('trello', {}).get('list_id'):
            self.log.debug(f'found {list_id=} in the config')
            return list_id

        # Fetching lists from Trello
        list_name = self._config['trello']['list_name']
        board_id = self._config['trello']['board_id']

        self.log.info('Fetching the target list by inspecting Trello.')
        self.log.debug(f'searching for {list_name=} in board with ID={board_id}')
        lists = self._retry_after_renewing_token(
            self._trello.boards.get_list, board_id)

        # Finding the appropriate list from the collection
        self.log.debug(f'searching for {list_name=} in lists: {lists}')
        try:
            list_id = [l['id'] for l in lists if l['name'] == 'IN'][0]
        except KeyError:
            self.log.error('Unrecognized format of list data from Trello!')
            self.log.warning('This error most likely requires patching the program code.')
            raise
        except IndexError:
            self.log.error(f'Could not find list with name "{list_name}"!')
            self.log.warning('Either the Trello workspace or the config is in an invalid state')
            self.log.info(f'Verify the Trello with ID={board_id} has a list with name={list_name}')
            raise

        # Update the config
        self.log.debug(f'Got {list_id=}. Persisting to the config.')
        self._config.update(section='trello', key='list_id', value=list_id)

        return list_id


class GUI:
    '''Wrap the Trello object in a simple GUI.'''

    log = logging.getLogger('quickIN.gui')

    def __init__(self, trello):
        self._trello = trello

    def _build_window(self):
        sg.theme("DarkBlue3")
        sg.set_options(font=("Courier New", 16))

        layout = [[sg.Text('Reminder: no description support yet')],
                  [sg.Input(key='in', do_not_clear=False, focus=True)]]
        window = sg.Window('Quick to IN', layout, finalize=True)
        window['in'].bind('<Return>', '_Return')
        return window

    def loop(self):
        window = self._build_window()

        # The main loop
        while True:
            match window.read():
                case (sg.WIN_CLOSED, _):
                    break
                case ('in_Return', values) if values.get('in') is not None:
                    self._trello.post_new_card(values.get('in'))
                    window['in'].set_focus()
                case event, values:
                    self.log.warning(f'Unrecognized GUI event: {event=}. Ignoring...')
                    self.log.debug(f'{event=} and {values=}')
                    window['in'].set_focus()

        window.close()
