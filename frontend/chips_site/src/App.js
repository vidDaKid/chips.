import { useState } from 'react';
import './App.css';

// Link for the websocket (add a game id)
const wsLink = 'ws://localhost:8000/ws/game/'

function App() {
	const [client, setClient] = useState()
	const [gameId, setGameId] = useState('')

	function connect(e) {
		const new_client = new WebSocket(wsLink + gameId + '/')
		new_client.onopen = () => {console.log('connected')};
		new_client.onmessage = (msg) => {console.log(msg)};
		new_client.onerror = (err) => {console.log(err)};
		new_client.onclose = () => {console.log('closed')};
		setClient(client)
	}

  return (
    <div className="App">
      <header className="App-header">
				<h1>chips.</h1>
				<input value={gameId} onChange={e=>setGameId(e.target.value.toUpperCase())} label='Game ID'/>
				<button onClick={connect}>Connect to Game</button>
      </header>
    </div>
  );
}

export default App;
