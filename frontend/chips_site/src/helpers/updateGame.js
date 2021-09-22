import React, { useContext } from 'react';
import { GameContext } from '../context/gameContext';

export default function UpdateGame(msg) {
	const action = JSON.parse(msg)
	const { players } = useContext(GameContext)

	const addPlayer = player => {
		players.concat(player)
	}

	switch (action.type) {
		case 'NEW_PLAYER':
			let newPlayer = {
				'player':action.player,
				'position':action.position,
				// 'c_count':action.c_count,
			}
			addPlayer(newPlayer)
			break

		case 'PLAYERS':
			addPlayer(action.players)
			break

		case 'SECRET':
			// setSecret(action.secret)
			localStorage.setItem('playerSecret', action.secret)
			// console.log('Player Secret: ' + secret)
			break

		case 'FAIL':
			alert(action.message)
			break

		default:
			console.log(`Unexpected type: ${action.type}`)
			break
	}
}
