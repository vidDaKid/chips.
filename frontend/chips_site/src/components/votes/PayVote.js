import React, { useContext, useState, useMemo } from 'react';
import { SocketContext } from '../../context/socketContext';
import { GameContext } from '../../context/gameContext';

export default function PayVote () {
	const { castBoolVote } = useContext(SocketContext)
	const { state, dispatch } = useContext(GameContext)
	const [ voting, setVoting ] = useState(false)

	// const showWinners = useMemo(() => {
		// let output = []
		// for (const pot in state.voteInfo.options) {
			// // output.push(<pre>{pot}: {state.voteInfo.options[pot]</pre>)
			// output.push('hi')
		// }
		// return output
	// }, [state.voteInfo])

	const castVote = (vote) => {
		setVoting(true)
		castBoolVote(vote)
	}

	return (
		<div className="PayVote">
			<p>Pay these winners ?</p>
			<button onClick={()=>console.log(state)}>CLICK</button>
			{state.voteInfo.options[-1]}
			{ voting ? <p>Waiting for votes...</p> : (
				<div className="voteButtons">
					<button onClick={()=>castVote(true)}>Yes</button>
					<button onClick={()=>castVote(false)}>No</button>
				</div>
			)}
		</div>
	)
}
