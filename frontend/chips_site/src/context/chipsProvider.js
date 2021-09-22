import { useCallback, useContext } from 'react';
import { WSLINK } from '../conf';
// import { gameReducer } from '../helpers/gameReducer';
import { gameStateZero } from '../helpers/gameStateZero';
import { createCall } from '../helpers/calls';
import { ChipsContext } from '../context/chipsContext';
import { GameContext } from '../context/gameContext';

export default function ChipsProvider () {
	const { dispatch } = useContext(GameContext)

	const onMessage = useCallback(msg => {
		dispatch(msg)
	})

	const onOpen = useCallback(() => {
		console.log('connected')
	}, [])

	const onClose = useCallback(() => {
		console.log('closed')
	}, [])

	const onError = useCallback(err => {
		console.log(err)
	}, [])

	const [connect, sendMessage] = useSocket(onOpen, onMessage, onClose, onError)
	
	// functions to send to server
	const joinGame = useCallback((gameId, name, position) => {
		createCall('JOIN', {gameId:gameId, name:name, position:position})
	}, [])

	const socketConnect = useCallback(() => {
		connect()
	}, [connect])

	return (
		<ChipsContext.Provider value={{socketConnect, joinGame}}>
		</ChipsContext.Provider>
	)
}
