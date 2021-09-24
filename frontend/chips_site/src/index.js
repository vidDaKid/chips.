import React, { useReducer, createContext, useState, useCallback } from 'react';
import ReactDOM from 'react-dom';
import { BrowserRouter as Router, Switch, Route } from 'react-router-dom'
import './styles/index.css';
import App from './components/App';
import Home from './components/Home';
import reportWebVitals from './reportWebVitals';
// import { SocketProvider } from './context/socketContext';
import { GameContext } from './context/gameContext';
import { gameStateZero } from './helpers/gameStateZero';
import { gameReducer } from './helpers/gameReducer';
import useSocket from './hooks/useSocket';
import { SocketContext } from './context/socketContext';
import { createCall } from './helpers/calls';

function Index() {
	const [ state, dispatch ] = useReducer(gameReducer, gameStateZero)

	const onMessage = useCallback(msg => {
		console.log(msg.data)
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
		dispatch(err)
	}, [])

	const [connect, sendMessage, socket] = useSocket(onOpen, onMessage, onClose, onError)
	
	// functions to send to server
	const joinGame = useCallback((name, position) => {
		sendMessage(createCall('JOIN', {name, position}))
	}, [sendMessage])

	const moveSeat = useCallback(position => {
		sendMessage(createCall('MOVE', {position}))
	}, [sendMessage])

	const startGame = useCallback(() => {
		sendMessage(createCall('START'))
	}, [sendMessage])
	
	const placeBet = useCallback(betSize => {
		sendMessage(createCall('BET', {betSize}))
	}, [sendMessage])

	const fold = useCallback(() => {
		sendMessage(createCall('FOLD'))
	}, [sendMessage])

	return (
		<GameContext.Provider value={{state, dispatch}}>
			<SocketContext.Provider value={{connect, joinGame, moveSeat, placeBet, fold, startGame, socket}}>
				<Router>
					<Switch>
						<Route exact path='/' component={Home} />
						<Route path='/game/:game_id/' component={App} />
					</Switch>
				</Router>
			</SocketContext.Provider>
		</GameContext.Provider>
	)
}

ReactDOM.render(
	<Index />,
  document.getElementById('root')
);

// If you want to start measuring performance in your app, pass a function
// to log results (for example: reportWebVitals(console.log))
// or send to an analytics endpoint. Learn more: https://bit.ly/CRA-vitals
reportWebVitals();
