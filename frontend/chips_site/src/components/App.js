import { useEffect, useCallback, useContext, useState } from 'react';
import { useParams } from 'react-router-dom';
import '../styles/App.css';
import { SocketContext } from '../context/socketContext';
import { GameContext } from '../context/gameContext';
import { MAX_PLAYERS, WSLINK } from '../conf';

function App() {
	const { connect, joinGame, moveSeat, placeBet, fold, startGame, socket } = useContext(SocketContext)
	const { state, dispatch } = useContext(GameContext)
	const [amount, setAmount] = useState('')
	const params = useParams()
	const gameId = params.game_id
	// const [socket, setSocket] = useState(null)
	// const secret = localStorage.getItem('playerSecret')

	// function connect () {
		// const ws = new WebSocket(WSLINK + gameId + '/')
		// setSocket(ws)
	// }

	const savePlayer = useCallback((e) => {
		e.returnValue = ''
		console.log('unloading...')
	}, [])

	useEffect(() => {
		// getSecret();
		connect(gameId);
		// console.log(socket)
		window.addEventListener('beforeunload', savePlayer);
		return () => {
			window.removeEventListener('beforeunload', savePlayer);
		}
	}, [connect])

	// useEffect(() => {
		// console.log(socket)
	// }, [socket])

	// async function getSecret() {
		// let s = localStorage.getItem('playerSecret');
		// if (s !== '') {
			// setSecret(s);
			// console.log('Secret: ' + secret);
			// console.log('S: ' + s);
		// }
	// }

	const range = (end) => {
		return Array.from({ length: end }, (_, idx) => idx)
	}

	function fillSeat(position) {
		// let tempPlayer = state.players.find(x => x.position === position)
		for (let tempPlayer of state.players) {
			if (tempPlayer.position === position) {
				return (
					<tr key={position}>
						<td>{tempPlayer.player==state.name ? 'true' : ''}</td>
						<td>{tempPlayer.player}</td>
						<td>{tempPlayer.c_count}</td>
						<td>{tempPlayer.player==state.dealer ? 'true' : ''}</td>
					</tr>
				)
			}
		}
		return (
			<tr key={position}>
				<td></td>
				<td className="tableName"><button onClick={()=>takeSeat(position)}>Take this seat</button></td>
				<td>N/A</td>
				<td />
			</tr>
		)
	}

	function takeSeat (position) {
		if (state.name) {
			moveSeat(position)
			return
		}
		let chosenName = prompt('whats ur name');
		console.log(chosenName)
		dispatch({type:'setName', name:chosenName})
		// socket.send({type:'JOIN',name:chosenName,position:position})
		joinGame(chosenName, position);
	}

	// if ( !client || client.readyState === WebSocket.CLOSED ) {
		// return (
			// <div className="App">
				// <h1 className="title">chips.</h1>
				// <p>Trying to connect to websocket...</p>
			// </div>
		// )
	// }

	if (!socket || socket.readyState == WebSocket.CLOSED) {
		return (
			<h3>Connecting to websocket...</h3>
		)
	}
  return (
    <div className="App">
			<h1 className="title">chips.</h1>
			<div className="playersTable">
				<h3>Table:</h3>
				<p>Pot Size: {state.pot}</p>
				<table className="tableElements">
					<thead>
						<tr>
							<th>Me</th>
							<th>Name</th>
							<th>ChipCount</th>
							<th>Dealer</th>
						</tr>
					</thead>
					<tbody>
						{range(MAX_PLAYERS).map(x => fillSeat(x))}
					</tbody>
				</table>
					{/*
					{players!==[] && players.map((player, idx) => <div key={idx}><tr>{player.player}</tr><tr>{player.c_count}</tr></div>)}
					*/}
			</div>
			{/*
			{!inGame && (
				<div className="joinGame">
					<label className="label">Pick a name to take a seat: </label>
					<br />
					<input value={name} onChange={e=>setName(e.target.value.toUpperCase())} />
					<button onClick={joinGame}>Take Seat</button>
				</div>
			)}
			*/}
			<button onClick={()=>console.log(state.players)}>PLAYERS</button>
			<button onClick={()=>startGame()}>START</button>
			<h4>Betting {'//'} {state.betRound.toUpperCase()}</h4>
			{state.toPlay.player === state.name ? (
				<div>
					<p>Owed: {state.toPlay.owed}</p>
					<div className="betButtons">
						<input label='bet amount' 
							value={amount} 
							onChange={e => setAmount(e.target.value)} />
						<button onClick={() => placeBet(amount)}>Play Bet</button>
						<button onClick={fold}>Fold</button>
					</div>
				</div>
			) : (
				<div className="toPlay">
					{state.toPlay.player!=='' &&
					<h4>To Play: {state.toPlay.player} owes {state.toPlay.owed}</h4>
					}
				</div>
		)}
		</div>
	)
}
export default App;
