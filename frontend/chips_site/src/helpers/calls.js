export function createCall (type, action) {
	let output = {}
	switch(type) {
		case "JOIN":
			// if (!action.hasOwnProperty('gameId') || !action.hasOwnProperty('name') || !action.hasOwnProperty('position')) return;
			output = {type:'JOIN', name:action.name, position:action.position}
			break
		
		case "SECRET_JOIN":
			if (!action.hasOwnProperty('secret')) return;
			output = {type:"SECRET_JOIN", secret:action.secret}
			break

		case "MOVE":
			output = {type:'MOVE', position:action.position}
			break

		case "BET":
			output = {type:"BET", bet_size:action.betSize}
			break

		// case 'START_CLAIMS':
			// output = {type:'START_CLAIMS', pot_id:action.potId}
			// break

		case 'CLAIM_WIN':
			output = {type:'CLAIM_WIN', pot_id:action.pot_id}
			break

		case 'VOTE':
			output = {type:'VOTE', vote:action.vote}
			break

		// send a message thats {type:action.type}
		default:
			output = {type}
	}
	return JSON.stringify(output)
}
