import { useState, useEffect, useMemo } from 'react';
import { useParams, useLocation} from 'react-router-dom';
import './App.css';

// Link for the websocket (add a game id)
const wsLink = 'ws://localhost:8000/ws/game/'

function App() {
	const [client, setClient] = useState()
	const [players, setPlayers] = useState([])
	const [inGame, setInGame] = useState(false)
	const [name, setName] = useState('')
	const [secret, setSecret] = useState('')
	// const [gameId, setGameId] = useState('')
	const params = useParams()
	// setGameId(params.game_id)
	const gameId = params.game_id
	
	// Get name from query params
	// const search = useLocation().search;
	// const name = new URLSearchParams(search).get('name');
	// useMemo(() => {
		// setGameId(params.game_id)
	// }, [params])

	async function connect() {
		const new_client = new WebSocket(wsLink + gameId + '/')
		new_client.onopen = () => {console.log('connected')};
		new_client.onmessage = (msg) => {handleMsg(msg)};
		new_client.onerror = (err) => {console.log(err)};
		new_client.onclose = () => {console.log('closed')};
		setClient(new_client)
		// get ur player if u got one
		if ( secret ) {
			await client.send(JSON.stringify({'type':'SECRET_JOIN','secret':secret}))
		}
	}

	useEffect(() => {
		getSecret();
		connect();
	}, [])

	// useMemo(() => {
		// const new_client = new WebSocket(wsLink + gameId + '/')
		// new_client.onopen = () => {console.log('connected')};
		// new_client.onmessage = (msg) => {handleMsg(msg)};
		// new_client.onerror = (err) => {console.log(err)};
		// new_client.onclose = () => {console.log('closed')};
		// setClient(new_client)
	// }, [gameId])

	function handleMsg(msg) {
		let parsedMsg = JSON.parse(msg.data)
		console.log(parsedMsg)
		switch (parsedMsg.type) {
			case 'NEW_PLAYER':
				setPlayers(state => state.concat([{'player':parsedMsg.player}]))
				break

			case 'PLAYERS':
				setPlayers(state => state.concat(parsedMsg.players))
				// console.log(parsedMsg.players)
				break

			case 'SECRET':
				setSecret(parsedMsg.secret)
				localStorage.setItem('secret', parsedMsg.secret)
				break

			case 'DEFAULT':
				console.log(`Unexpected type: ${parsedMsg.type}`)
				break
		}
	}

	function getSecret() {
		let s = localStorage.getItem('secret');
		if (s !== '') {
			setSecret(s);
			console.log(s);
		}
	}

	async function joinGame() {
		await client.send(JSON.stringify({'type':'JOIN','name':name}));
		setInGame(true);
		console.log('joining game...')
	}

	// if(!inGame) {
		// return (
			// <div>
				// <label>Name:</label>
				// <input value={name} onChange={e=>setName(e.target.value)} />
			// </div>
		// )
	// }
  return (
    <div className="App">
			<h1 className="title">chips.</h1>
			<div className="table">
				<h3>Players:</h3>
				<ul>
					{players!==[] && players.map((player, idx) => <li key={idx}>{player.player}</li>)}
				</ul>
			</div>
			{!inGame && (
				<div className="joinGame">
					<label className="label">Pick a name to take a seat: </label>
					<br />
					<input value={name} onChange={e=>setName(e.target.value.toUpperCase())} />
					<button onClick={joinGame}>Take Seat</button>
				</div>
			)}
			<button onClick={()=>console.log(secret)}>SECRET</button>
    </div>
  );
}

export default App;
