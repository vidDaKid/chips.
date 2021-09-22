import { useState } from 'react';
import { WSLINK } from '../conf';

export default function useSocket (onOpen, onMessage, onClose, onError) {
	const [socket, setSocket] = useState(null)
	
	const connect = () => {
		const ws = WebSocket(WSLINK)
		ws.onopen = onOpen
		ws.onmessage = onMessage
		ws.onclose = onClose
		ws.onerror = onError
		setSocket(ws)
	}

	const sendMessage = (msg) => {
		socket.send(msg)
	}

	return [connect, sendMessage]
}
