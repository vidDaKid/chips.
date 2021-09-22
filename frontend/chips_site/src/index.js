import React, { useReducer } from 'react';
import ReactDOM from 'react-dom';
import { BrowserRouter as Router, Switch, Route } from 'react-router-dom'
import './styles/index.css';
import App from './components/App';
import Home from './components/Home';
import reportWebVitals from './reportWebVitals';
import { ChipsProvider } from './context/chipsContext';
import { GameContext } from './context/gameContext';
import { gameStateZero } from './helpers/gameStateZero';
import { gameReducer } from './helpers/gameReducer';

function Index() {
	const [state, dispatch] = useReducer(gameReducer, gameStateZero)

	return (
		<GameContext.Provider value={{...state, dispatch}}>
			<ChipsProvider>
				<Router>
					<Switch>
						<Route exact path='/' component={Home} />
						<Route path='/game/:game_id/' component={App} />
					</Switch>
				</Router>
			</ChipsProvider>
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
