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

		case "START":
			output = {type:"START"}
			break

		case "BET":
			output = {type:"BET", bet_size:action.betSize}
			break

		case "FOLD":
			output = {type:"FOLD"}
			break

		default:
			output = {type}
	}
	return JSON.stringify(output)
}
