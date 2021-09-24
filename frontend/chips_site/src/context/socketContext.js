import { useCallback, useContext, createContext } from 'react';
// import { WSLINK } from '../conf';
// import { gameReducer } from '../helpers/gameReducer';
// import { gameStateZero } from '../helpers/gameStateZero';
import { createCall } from '../helpers/calls';
import { GameContext } from '../context/gameContext';
import useSocket from '../hooks/useSocket';
// import updateGame from '../helpers/updateGame';

export const SocketContext = createContext();

export function SocketProvider () {
	const { state, dispatch } = useContext(GameContext)

	const onMessage = useCallback(msg => {
		let action = JSON.parse(msg.data)
		dispatch(action)
	})

	const onOpen = useCallback(() => {
		console.log('connected')
	}, [])

	const onClose = useCallback(() => {
		console.log('closed')
	}, [])

	const onError = useCallback(err => {
		let error = JSON.parse(err)
		dispatch(error)
	}, [])

	const [connect, sendMessage] = useSocket(onOpen, onMessage, onClose, onError)
	
	// functions to send to server
	const joinGame = useCallback((gameId, name, position) => {
		sendMessage(createCall('JOIN', {gameId, name, position}))
	}, [sendMessage])

	const socketConnect = useCallback(() => {
		connect()
	}, [connect])

	return (
		<SocketContext.Provider value={{socketConnect, joinGame}}>
		</SocketContext.Provider>
	)
}
