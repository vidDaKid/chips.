import React, { useContext, useEffect, useState } from 'react';
import { GameContext } from '../context/gameContext';
import { SocketContext } from '../context/socketContext';

export default function Winners({ props }) {
	const { state, dispatch } = useContext(GameContext)
	const { claimWin } = useContext(SocketContext)

	const claimPotWin = () => {
		let currPotId = props.potId - 1
		let truePotId = JSON.parse(state.pots[currPotId]).id
		claimWin(truePotId)
	}
	
	return (
		<div className="Winners">
			<button onClick={claimPotWin}>Claim Win</button>
		</div>
	)
}
