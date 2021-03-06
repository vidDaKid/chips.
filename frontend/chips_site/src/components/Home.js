import { useState, useEffect, useContext } from 'react';
import { useHistory } from 'react-router-dom';
import { GameContext } from '../context/gameContext';
import { SocketContext } from '../context/socketContext';
import '../styles/Home.css';

function Home() {
	const [gameId, setGameId] = useState('')
	const [join, setJoin] = useState(false)
	const {state, dispatch} = useContext(GameContext);
	// const { socketConnect, joinGame } = useContext(SocketContext);
	const history = useHistory()

	function newGameId() {
		// creaets a random 8 character string to use as the gameId
		const randomGameId = Math.random().toString(16).substr(2,10).toUpperCase();
		return randomGameId
		// setGameId(randomGameId)
	}

	// if (gameId != '' && name != '') {
		// const redirectLink = `/game/${gameId}/?name=${name}`
		// return <Redirect to=redirectLink />
	// }

	function createGame() {
		let randomGameId = newGameId()
		let path = `/game/${randomGameId}/`;
		history.push(path);
	}

	function joinGame() {
		let path = `game/${gameId}/`;
		history.push(path);
	}

	// temp for testing
	// return (
		// <div>
			// <h1>chips.</h1>
			// <button onClick={() => dispatch({type:'NEW_PLAYER', player:'vee',})}>test reducer</button>
			// <pre>{state.players}</pre>
		// </div>
	// )

	return (
		<div className="main">
			<h1 className="title">chips.</h1>
			<div className="choices">
				<div className="createGame">
					<button onClick={createGame} className="btn btnCreate">
						Create Game
					</button>
				</div>
				<div className="joinGame">
					{join ? (
						<div>
							<label for='gameId' className="label">Game ID: </label>
							<input 
								value={gameId} 
								onChange={e=>setGameId(e.target.value)}
								label='Game ID: ' />
							<button onClick={joinGame}>Join Game</button>
						</div>
					) : (
						<button onClick={() => setJoin(true)} className="btn btnJoin">
							Join Game
						</button>
					)}
				</div>
			</div>
		</div>
	)
}

export default Home;
