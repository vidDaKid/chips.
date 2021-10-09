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

		case 'SETTINGS':
			return {...state, settings:action.settings}

			// announces teh dealer, small blind and big blind each round
		case 'POSITIONS':
			// add the bet for the blinds
			let playerBlinds = new Set()
			// console.log(action)
			state.players.forEach(i => {
				// console.log('player: ' + i.player + ' sb: ' + action.small_blind)
				if (i.player == action.positions.small_blind) {
					// console.log('small blind: ' + i.player)
					playerBlinds.add({...i, c_count:i.c_count-Math.round(state.settings.big_blind/2)})
				} else if (i.player == action.positions.big_blind) {
					// console.log('big blind: ' + i.player)
					playerBlinds.add({...i, c_count:i.c_count-state.settings.big_blind})
				} else {
					// console.log('other:' + i.player)
					playerBlinds.add({...i})
				}
				return null
			})
			// console.log(playerBlinds)
			return {...state, dealer: action.positions.dealer, players:playerBlinds}

		// case 'DECIDE_WINNERS':
			// return {...state, decideWinner: true, inRound: false, options:action.options, claimed: false}

		// case 'VOTE_WINNERS':
			// return {...state, voteWinner: true, decideWinner:false, options: action.eligible}

		// case 'START_CLAIMS':
			// return {...state, decideWinner: true}

		case 'POTS':
			// let jsonPots = new Array()
			// action.pots.forEach(x => json.Pots.push(JSON.parse(x)))
			return {...state, decideWinner:true, inRound:false, pots:action.pots}

		// case 'WINNER':
			// // pay out winner
			// let paidPlayers = new Set()
			// state.players.forEach(x => {
				// paidPlayers.add(
					// x.player===action.player ? {...x, c_count:x.c_count+action.amount} : x
				// )
			// })
			// return {...state, players:paidPlayers}

			// Says who's turn it is to play
		case 'TO_PLAY':
			return {...state, toPlay: {player:action.player, owed:action.owed}}

		// round info 
		case "NEW_BET_ROUND":
			return {...state, betRound: action.bet_round}

		case "NEW_ROUND":
			return {...state, betRound: "pre-flop", inRound:true, decideWinner:false}

		case "PAY_OUT":
			// let unpaidPlayers = new Set()
			// state.players.map(x => unpaidPlayers.add({...x, claimed: true}))
			let paidOutPlayers = new Set()
			state.players.forEach(x => {
				let paidOutPlayer = action.players.find(y => y.player === x.player)
				paidOutPlayers.add({...x, c_count:paidOutPlayer.c_count})
			})
			return {...state, inRound: false, decideWinner: false, voteWinner: false, claimed:false, options:{}, players:paidOutPlayers}

			// betting info
		case "PREV_BET":
			// take away chips from player who bet
			let updatedPlayers = new Set()
			state.players.forEach(x => {
				updatedPlayers.add(
					x.player==action.player ? (
						{...x, c_count:x.c_count-action.bet_size} 
					) : x
				)
			})
			// add bet to the game state pot
			return {...state, players:updatedPlayers, pot:state.pot+action.bet_size}

		case "CLAIMED_WIN":
			let updatedPotOptions
			if (state.options.hasOwnProperty(action.pot_id)) {
				updatedPotOptions = new Array(state.options[action.pot_id])
			} else {
				updatedPotOptions = new Array()
			}
			updatedPotOptions.push(action.player)
			let newFullOptions = {...state.options}
			newFullOptions[action.pot_id] = updatedPotOptions
			return {...state, options:newFullOptions}

		case "END_VOTE":
			return {...state, vote:false, voteType:'', voteInfo: {}}

		case "FAILED_VOTE":
			return {...state, vote:false, voteType:'', voteInfo: {}}

		case "VOTE_PAY":
			return {...state, vote:true, voteType:'PAY', voteInfo:{options:action.options}}

		case "FOLD":
			return {...state}

		case 'FAIL':
			alert(action.message)
			return state

		case 'setName':
			return {...state, name:action.name}

		case 'startGame':
			return {...state, inRound: true}

		case 'claimed':
			return {...state, claimed: true}

		default:
			console.log(`Unexpected type: ${action.type}`)
			// console.log(action)
			return state
	}
}
