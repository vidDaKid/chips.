export function createCall (type, action) {
	switch(type) {
		case "JOIN":
			if (!action.hasOwnProperty('gameId') || !action.hasOwnProperty('name') || !action.hasOwnProperty('position')) return;
			return {type:'JOIN', name:action.name, position:action.position, gameId:action.gameId}
		
		case "SECRET_JOIN":
			if !action.hasOwnProperty('secret') return;
			return {type:"SECRET_JOIN", secret:action.secret}

		case default:
			return
	}
}
