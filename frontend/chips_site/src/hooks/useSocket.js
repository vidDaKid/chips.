import { useState, useCallback } from 'react';
import { WSLINK } from '../conf';

export default function useSocket (onOpen, onMessage, onClose, onError) {
	const [socket, setSocket] = useState(null)
	
	const connect = useCallback(gameId => {
		const ws = new WebSocket(WSLINK + gameId + '/')
		ws.onopen = onOpen
		ws.onmessage = onMessage
		ws.onclose = onClose
		ws.onerror = onError
		// if (ws && ws.readyState == WebSocket.OPEN) {
		setSocket(ws)
		// }
	}, [setSocket])

	const sendMessage = useCallback((msg) => {
		if (socket.readyState!==WebSocket.OPEN) return;
		socket.send(msg)
	}, [socket])

	return [connect, sendMessage, socket]
}
