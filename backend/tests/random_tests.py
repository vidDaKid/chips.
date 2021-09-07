from websocket import create_connection, WebSocketApp, WebSocket
import asyncio, json

LINK = "ws://localhost:8000/ws/game/"
GAME_ID = "SMH123"
GAME_ENDPOINT = "ws/game/" + GAME_ID + "/"
F_LINK = LINK + GAME_ENDPOINT

# Action data
# CREATE = {'action'{'type':'CREATE','settings':{'game_id':
# JOIN = {'action': {'type': 'JOIN', 'game_id': GAME_ID, 'name':'2v'}}
# COUNT = {'action':{'type':'COUNT', 'game_id': GAME_ID}}
# D_COUNT = json.dumps(COUNT)
# STATUS = {'action': {'type':'STATUS', 'game_id':GAME_ID}}
# D_STATUS = json.dumps(STATUS)
# CREATE = {'action': {'type': 'CREATE','game_id':GAME_ID,'settings':{
        # 'default_count':'200',
        # 'big_blind':'4'}}}
# D_CREATE = json.dumps(CREATE)

def make_action(typ,*args,**kwargs) -> 'json(dict)':
    d = {'type':typ}
    for x,y in kwargs.items():
        d[x] = y
    return json.dumps(d)

def test_count(name:str, create:bool=False, game_id:str=None):
    ws = WebSocket()
    ws.connect(LINK)
    ws.recv()
    if create==True:
        ws.send(make_action('CREATE'))
        game = ws.recv()
        print('Created Game')
        game = json.loads(game)
        if game['status']=='ok':
            game_id = game['body']['game_id']
        else:
            print(game['message'])
        print(f'{game_id=}')
    else:
        if not game_id:
            print('Add Game ID To Join')
            return
    ws.send(make_action('JOIN',game_id=game_id, name=name))
    print(ws.recv())
    # if create==True:
        # ws.send(make_action('ORDER',game_id=game_id))
        # print(ws.recv())
    # count_me(ws, game_id)
    return ws

def order(ws, game_id):
    ws.send(make_action('ORDER',game_id=game_id))
    print(ws.recv())

def count(ws, game_id:str):
    ws.send(make_action('COUNT', game_id=game_id))
    print(ws.recv())
    return
