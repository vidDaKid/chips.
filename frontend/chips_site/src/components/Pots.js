import React, { useContext, useState, useEffect } from 'react';
import { GameContext } from '../context/gameContext';
import { SocketContext } from '../context/socketContext';
import Winners from './Winners';

export default function Pots() {
	const { state, dispatch } = useContext(GameContext);
	const { payWinners } = useContext(SocketContext);
	const [ potId, setPotId ] = useState(1)
	const [ winner, setWinner ] = useState(false)

	useEffect(() => {
		JSON.parse(state.pots[potId-1]).eligible.forEach(x => {
			if(x == state.name) {
				setWinner(true)
			}
		})
	}, [potId])

	return (
		<div className="Winners">
			<h4>pots.</h4>
			<div>
				{ state.pots.map((x,idx) => <button onClick={()=>setPotId(idx+1)} key={idx}>Pot {idx+1}</button> )}
			</div>
			<p>Pot {potId}</p>
			{/*
			<p>Options</p>
			<ul>
				{
					JSON.parse(state.pots[potId-1])
						.eligible.map((x,idx) => <li key={idx}>{x}</li>)
				}
			</ul>
			*/}
			{ winner ? (
				<Winners props={{ potId }} />
			) : (
				<p>Loser</p>
			)}
			{/* state.decideWinner ? (
				JSON.parse(state.pots[potId-1]).eligible.forEach(x => x==state.name &&
					<Winners />
				)
			) : (
				<button onClick={()=>startClaims(potId)}>Start Deciding Winners</button>
			)*/}
			<pre>Options: {JSON.parse(state.pots[potId-1]).eligible}</pre>
		  <pre>Claimed Winners: { state.options[JSON.parse(state.pots[potId-1]).id] }</pre>
			<button onClick={payWinners}>Pay Winners</button>
		</div>
	)
}
