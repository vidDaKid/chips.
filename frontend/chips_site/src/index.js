import React from 'react';
import ReactDOM from 'react-dom';
import { BrowserRouter as Router, Switch, Route } from 'react-router-dom'
import './index.css';
import App from './App';
import Home from './Home';
import reportWebVitals from './reportWebVitals';

function Index() {
	return (
		<Router>
			<Switch>
				<Route exact path='/' component={Home} />
				<Route path='/game/:game_id/' component={App} />
			</Switch>
		</Router>
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
