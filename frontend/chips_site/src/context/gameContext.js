import { createContext } from 'react';
import { gameStateZero } from '../helpers/gameStateZero';
import { updateGame } from '../helpers/updateGame';

export const GameContext = createContext();

export const GameProvider = () => {
	const [state, dispatch] = useReducer(updateGame, gameStateZero)

	return (
		<GameContext.Provider value={{...state, dispatch}}>
		</GameContext.Provider>
	)
}
