import { useContext } from 'react';
import { ChipsContext } from '../context/chipsContext';

export default function updateGame(msg) {
	const [{name, position, players}, setGameState] = useContext(ChipsContext)
	const action = JSON.parse(msg)

	function addPlayer = useCallback((player) => {
		setGameState(cState => {...cState, players: [...cState.players, player]})
	}, [setGameState])

	switch (action.type) {
		case 'NEW_PLAYER':
			let new_player = {
				'player':action.player,
				'position':action.position,
				// 'c_count':action.c_count,
			}
			addPlayer(new_player)
			break

		case 'PLAYERS':
			action.players.forEach(x => addPlayer(x))
			// console.log(action.players)
			break

		case 'SECRET':
			// setSecret(action.secret)
			localStorage.setItem('playerSecret', action.secret)
			// console.log('Player Secret: ' + secret)
			break

		case 'FAIL':
			alert(action.message)
			break

		default:
			console.log(`Unexpected type: ${action.type}`)
			break
	}
}
