export function gameReducer (state, action) {
	switch(action.type) {
		// Everything in caps is coming from the server, lowercase is whithin the app (might make this 2 functions eventually)
			// Player JOINED
		case 'NEW_PLAYER':
			let newPlayer = {
				'player':action.player,
				'position':action.position,
				'c_count':action.c_count,
			}
			return {...state, players:new Set(state.players).add(newPlayer)}

			// player left
		case 'PLAYER_LEAVE':
			let newPlayers = new Set()
			state.players.forEach(x => x.player!==action.player && newPlayers.add(x))
			// console.log(action.player)
			// console.log(newPlayers)
			return {...state, players:newPlayers }

			// players that are at the table u just joined
		case 'PLAYERS':
			let newPlayerSet = new Set(state.players)
			action.players.forEach(x => newPlayerSet.add(x))
			return {...state, players:newPlayerSet}

			// ur players secret key so u can join back
		case 'SECRET':
			// setSecret(action.secret)
			localStorage.setItem('playerSecret', action.secret)
			// console.log('Player Secret: ' + secret)
			return state

			// announces teh dealer, small blind and big blind each round
		case 'POSITIONS':
			return {...state, dealer: action.positions.dealer}

			// Says who's turn it is to play
		case 'TO_PLAY':
			return {...state, toPlay: {player:action.player, owed:action.owed}}

		// round info 
		case "NEW_BET_ROUND":
			return {...state, betRound: action.bet_round}

		case "NEW_ROUND":
			return {...state, betRound: "pre-flop"}

			// betting info
		case "PREV_BET":
			// take away chips from player who bet
			let updatedPlayers = new Set()
			state.players.forEach(x => updatedPlayers.add(x.player==action.player ? {player:x.player, c_count:x.c_count-action.bet_size, position:x.position} : x))
			// add bet to the game state pot
			return {...state, players:updatedPlayers, pot:state.pot+action.bet_size}

		case 'FAIL':
			alert(action.message)
			return state

		case 'setName':
			return {...state, name:action.name}

		case 'testing':
			console.log(state)
			return state

		default:
			console.log(`Unexpected type: ${action.type}`)
			return state
	}
}
