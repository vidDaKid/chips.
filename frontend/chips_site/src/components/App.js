import { useEffect, useCallback, useContext, useState } from 'react';
import { useParams } from 'react-router-dom';
import '../styles/App.css';
import { SocketContext } from '../context/socketContext';
import { GameContext } from '../context/gameContext';
import { MAX_PLAYERS, WSLINK } from '../conf';
import Bet from './Bet';
import Pots from './Pots';
import Winners from './Winners';
import Vote from './Vote';

function App() {
	const { connect, claimWin, joinGame, moveSeat, placeBet, fold, startGame, socket } = useContext(SocketContext)
	const { state, dispatch } = useContext(GameContext)
	// const [claimed, setClaimed] = useState(false)
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
		window.addEventListener('beforeunload', savePlayer);
		return () => {
			window.removeEventListener('beforeunload', savePlayer);
		}
	}, [connect])

	// reset claimed state each time we update the options
	// useEffect(() => {
		// setClaimed(false)
	// }, [state.options])

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
				<td />
				<td className="tableName"><button onClick={()=>takeSeat(position)}>Take this seat</button></td>
				<td />
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
		// console.log(chosenName)
		dispatch({type:'setName', name:chosenName})
		joinGame(chosenName, position);
	}

	if (!socket || socket.readyState == WebSocket.CLOSED) {
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
			</div>
			{ !state.inRound && <button onClick={startGame}>START</button> }
			{ state.inRound && <Bet /> }
			{ state.decideWinner && <Pots/> }
			{ state.vote && <Vote /> }
			{/* state.decideWinner &&
					<div>
						<h4>Decide Winner</h4>
						<p>Pots</p>
						<pre>{state.pots}</pre>
						<h5>Options: {state.options.map((x,i) => i==state.options.length-1 ? x : x,)}</h5>
						{ state.options.find(x => x==state.name) ? (
							<div>
								{state.claimed ? (
									<p>Waiting for your winnings</p>
								) : (
									<button onClick={claimWin}>Claim Win</button>
								)}
							</div>
						) : ( 
							<p>Loser</p>
						)}
					</div>
			*/}
			{/* state.voteWinner && (
				<div>
					<h4>Vote for Winner</h4>
					<p>Options:</p>
					{ state.options.map(x => <pre>{x}</pre>) }
				</div>
			)*/}
		</div>
	)
}
export default App;
