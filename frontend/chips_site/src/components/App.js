import { useState, useEffect, useMemo, useCallback } from 'react';
import { useParams, useLocation} from 'react-router-dom';
import { useSocket } from '../hooks/useSocket';
import '../styles/App.css';
import { ChipsContext } from '../context/chipsContext';
import { GameContext } from '../context/gameContext';

function App() {
	const { socketConnect, joinGame } = useContext(ChipsContext)
	const { name, players, dispatch } = useContext(GameContext)
	const params = useParams()
	const gameId = params.game_id
	// const secret = localStorage.getItem('playerSecret')

	useEffect(() => {
		// getSecret();
		socketConnect();
	}, [])

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
		let tempPlayer = players.find(x => x.position === position)
		if (tempPlayer) {
			return (
				<tr key={position}>
					<td>{tempPlayer.player}</td>
					<td>{tempPlayer.c_count}</td>
				</tr>
			)
		}
		return (
			<tr key={position}>
				<td className="tableName"><button onClick={()=>takeSeat(position)}>Take this seat</button></td>
				<td>N/A</td>
			</tr>
		)
	}

	function takeSeat (position) {
		let name = prompt('whats ur name');
		console.log(name)
		joinGame(name, position);
	}

	if ( !client || client.readyState === WebSocket.CLOSED ) {
		return (
			<div className="App">
				<h1 className="title">chips.</h1>
				<p>Trying to connect to websocket...</p>
			</div>
		)
	}

  return (
    <div className="App">
			<h1 className="title">chips.</h1>
			<div className="table">
				<h3>Players:</h3>
				<table>
					<thead>
						<tr>
							<th>Name</th>
							<th>ChipCount</th>
						</tr>
					</thead>
					<tbody>
						{range(maxPlayers).map(x => fillSeat(x))}
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
			<button onClick={()=>console.log(players)}>PLAYERS</button>
    </div>
  );
}

export default App;
