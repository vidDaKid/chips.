import React, { useContext } from 'react';
import { GameContext } from '../context/gameContext';
import { SocketContext } from '../context/socketContext';

export default function Winners() {
	const { state, dispatch } = useContext(GameContext);
	const { } = useContext(SocketContext);

	return (
		<div className="Winners">
			<h4>Deciding Winners</h4>
			<p>Pots:</p>
			<pre>{ state.pots }</pre>
		</div>
	)
}
