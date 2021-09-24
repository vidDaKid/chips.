import React, { useState, useContext } from 'react';
import { GameContext } from '../context/gameContext';
import { SocketContext } from '../context/socketContext';

export default function Bet () {
	const { state, dispatch } = useContext(GameContext)
	const { placeBet, fold } = useContext(SocketContext)
	const [amount, setAmount] = useState('')
	/*
	return (
		<div>
			<h1>test</h1>
			<h4>Betting {'//'} {state.betRound.toUpperCase()}</h4>
			{state.toPlay.player != '' && state.toPlay.player == state.name ? (
				<p>true</p>
			):(
				<p>false</p>
			)}
		<button onClick={()=>console.log(state.name)}>h</button>
		</div>
	) */

	// used to create a slider or an error function b4 sending to server
	// delete if not used
	function getMaxChips() {
		for (const i in state.players) {
			if (i.player == state.name) {
				return i.c_count
			}
		}
		return 0
	}

	return (
		<div>
			<h4>Betting {'//'} {state.betRound.toUpperCase()}</h4>
			{state.toPlay.player != '' && state.toPlay.player == state.name ? (
				<div>
					<p>Owed: {state.toPlay.owed}</p>
					<div className="betButtons">
						<input label='bet amount' 
							value={amount} 
							onChange={e => setAmount(e.target.value)} 
							type='number' />
						<button onClick={() => placeBet(amount)}>Play Bet</button>
						<button onClick={fold}>Fold</button>
					</div>
				</div>
			) : (
				<div className="toPlay">
					{state.toPlay.player!=='' &&
					<h4>To Play: {state.toPlay.player} owes {state.toPlay.owed}</h4>
					}
				</div>
			)}
		</div>
	)
}
