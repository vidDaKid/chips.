import React, { useContext, useMemo } from 'react';
import { GameContext } from '../context/gameContext';
import PayVote from './votes/PayVote';
import '../styles/Vote.css';

// Creates a vote modal & populates it w the relevant info
export default function Vote () {
	const { state, dispatch } = useContext(GameContext);

	const voteTypeComponent = useMemo(() => {
		switch (state.voteType) {
			case 'PAY':
				return <PayVote />
			
			default:
				return <p>Error. No Voting Type.</p>
		}
	}, [state.voteType])

	return (
		<div className="Vote">
			<div className="overlay"></div>
			<div className="voteModal">
				<h4>vote.</h4>
				{voteTypeComponent}
			</div>
		</div>
	)
}
