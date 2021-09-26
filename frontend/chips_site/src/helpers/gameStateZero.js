export const gameStateZero = {
	name: '',
	dealer: '',
	betRound: 'pre-flop',
	decideWinner: false,
	inRound: false,
	pot: 0,
	players: new Set(),
	toPlay: { player: '', owed: 0 },
	settings: {},
	options: new Array(),
}
