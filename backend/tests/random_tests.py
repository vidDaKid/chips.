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

def test_create(ws=None):
    if not ws:
        ws = WebSocket()
        # try:
        ws.connect(LINK)
        # except Exception as e:
            # print('[FAILED TO CONNECT TO LINK]')
            # print(e)
            # return
        # ws.recv()
    # try:
    ws.send(make_action('CREATE'))
    # except Exception as e:
        # print('[FAILED TO SEND ACTION TO TCP SERVER]')
        # print(e)
        # return
    # try:
    game = ws.recv()
    # except Exception as e:
        # print('[FAILED TO CONNECT TO GAME]')
        # print(e)
        # return
    if game:
        print('='*8, 'CREATED GAME', '='*8)
        print(game)
    # return game['game_id']
    return ws

def test_join(game_id:str, name:str='vee', ws=None):
    if not ws:
        ws = WebSocket()
        ws.connect(LINK)
    ws.send(make_action('JOIN',name=name,game_id=game_id))
    info = ws.recv()
    print(info)
    return ws

def start_order(ws:'WebSocket', game_id:str):
    ws.send(make_action('ORDER', game_id=game_id))
    return ws

def count_me(ws:'WebSocket', game_id:str):
    ws.send(make_action('COUNT', game_id=game_id))
    return ws

def start_vote(ws:'WebSocket', game_id:str, vote_param:str):
    ws.send(make_action('START_VOTE',game_id=game_id,voting_param=vote_param))
    return ws

def cast_vote(ws:'WebSocket', game_id:str, vote:bool):
    ws.send(make_action('VOTE',game_id=game_id,vote=vote))
    return ws

# def test_full_vote(create:bool=False, game_id:str=None,name:str='vee'):
    # ws = WebSocket()
    # ws.connect(LINK)
    # if create:
        # game_id = test_create(ws)
        # print(game_id)
    # ws = test_join(ws=ws,game_id=game_id,name=name)

# def send_count(ws:'WebSocket', game_id:str):
    # ws.send(make_action('COUNT', game_id=game_id))
    # return ws
# 
# def test_count(name:str, create:bool=False, game_id:str=None):
    # ws = WebSocket()
    # ws.connect(LINK)
    # ws.recv()
    # if create==True:
        # ws.send(make_action('CREATE'))
        # game = ws.recv()
        # print('Created Game')
        # game = json.loads(game)
        # if game['status']=='ok':
            # game_id = game['body']['game_id']
        # else:
            # print(game['message'])
        # print(f'{game_id=}')
    # else:
        # if not game_id:
            # print('Add Game ID To Join')
            # return
    # ws.send(make_action('JOIN',game_id=game_id, name=name))
    # print(ws.recv())
    # # if create==True:
        # # ws.send(make_action('ORDER',game_id=game_id))
        # # print(ws.recv())
    # # count_me(ws, game_id)
    # return ws

# def order(ws, game_id):
    # ws.send(make_action('ORDER',game_id=game_id))
    # print(ws.recv())
    # return ws

# def count(ws, game_id:str):
    # ws.send(make_action('COUNT', game_id=game_id))
    # print(ws.recv())
    # return ws
