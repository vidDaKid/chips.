export function gameReducer (state, action) {
	switch(action.type) {
		case 'NEW_PLAYER':
			let newPlayer = {
				'player':action.player,
				'position':action.position,
				// 'c_count':action.c_count,
			}
			return state.players.concat(newPlayer)

		case 'PLAYERS':
			return state.players.concat(action.players)

		case 'SECRET':
			// setSecret(action.secret)
			localStorage.setItem('playerSecret', action.secret)
			// console.log('Player Secret: ' + secret)
			return state

		case 'FAIL':
			alert(action.message)
			return state

		case 'setName':
			return {...state, name:action.name}

		default:
			console.log(`Unexpected type: ${action.type}`)
			return state
	}
}
