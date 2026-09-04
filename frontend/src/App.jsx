import { useState, useEffect, useRef } from 'react'
import './App.css'

const SUITS = ['Hearts', 'Diamonds', 'Clubs', 'Spades']
const BACKEND_HTTP = import.meta.env.VITE_BACKEND_HTTP || 'http://127.0.0.1:8000'
const BACKEND_WS = import.meta.env.VITE_BACKEND_WS || 'ws://127.0.0.1:8000'

function App() {
  const [screen, setScreen] = useState('landing') // 'landing' | 'game'
  const [playerName, setPlayerName] = useState('')
  const [joinCodeInput, setJoinCodeInput] = useState('')
  const [roomCode, setRoomCode] = useState(null)
  const [myRole, setMyRole] = useState(null)
  const [gameState, setGameState] = useState(null)
  const [connected, setConnected] = useState(false)
  const [errorMessage, setErrorMessage] = useState(null)
  const wsRef = useRef(null)

  const connectToRoom = (code) => {
    const ws = new WebSocket(`${BACKEND_WS}/ws/${code}/${playerName}`)
    wsRef.current = ws

    ws.onopen = () => {
      console.log(`Connected to room ${code}`)
      setConnected(true)
    }

    ws.onmessage = (event) => {
      const data = JSON.parse(event.data)
      console.log('Received:', data)

      if (data.type === 'role_assigned') {
        setMyRole(data.role)
      } else if (data.type === 'error') {
        setErrorMessage(data.message)
        setTimeout(() => setErrorMessage(null), 3000)
      } else {
        setGameState(data)
      }
    }

    ws.onclose = (event) => {
      console.log('Disconnected. Close code:', event.code)
      setConnected(false)
      if (event.code === 4404) setErrorMessage('Room not found')
      if (event.code === 4403) setErrorMessage('Room is full')
    }

    setRoomCode(code)
    setScreen('game')
  }

  const handleCreateRoom = async () => {
    if (!playerName) {
      setErrorMessage('Enter your name first')
      return
    }
    const response = await fetch(`${BACKEND_HTTP}/create_room`, { method: 'POST' })
    const data = await response.json()
    connectToRoom(data.room_code)
  }

  const handleJoinRoom = () => {
    if (!playerName || !joinCodeInput) {
      setErrorMessage('Enter your name and a room code')
      return
    }
    connectToRoom(joinCodeInput.toUpperCase())
  }

  useEffect(() => {
    return () => {
      if (wsRef.current) wsRef.current.close()
    }
  }, [])

  const handleChooseTrump = (suit) => {
    wsRef.current.send(JSON.stringify({ type: 'choose_trump', suit: suit }))
  }

  const handlePlayCard = (card) => {
    wsRef.current.send(JSON.stringify({ type: 'play_card', card: card }))
  }

  if (screen === 'landing') {
    return (
      <div className="App">
        <h1>3-2-5 Card Game</h1>

        {errorMessage && <p style={{ color: 'red' }}>⚠️ {errorMessage}</p>}

        <div>
          <label>Your name: </label>
          <input
            type="text"
            value={playerName}
            onChange={(e) => setPlayerName(e.target.value)}
          />
        </div>

        <div style={{ marginTop: '1rem' }}>
          <button onClick={handleCreateRoom}>Create Room</button>
        </div>

        <div style={{ marginTop: '1rem' }}>
          <input
            type="text"
            placeholder="Room code"
            value={joinCodeInput}
            onChange={(e) => setJoinCodeInput(e.target.value)}
          />
          <button onClick={handleJoinRoom}>Join Room</button>
        </div>
      </div>
    )
  }

  const isMyTurn = gameState?.whose_turn === myRole

  return (
    <div className="App">
      <h1>3-2-5 Card Game</h1>
      <p>Room code: <strong>{roomCode}</strong> (share this with friends)</p>
      <p>Playing as: <strong>{myRole || 'assigning...'}</strong> ({playerName})</p>
      <p>Backend connection: {connected ? '✅ Connected' : '❌ Not connected'}</p>

      {errorMessage && <p style={{ color: 'red' }}>⚠️ {errorMessage}</p>}

      {gameState && myRole && (
        <div>
          <p>Phase: {gameState.phase}</p>
          <p>Trump suit: {gameState.trump_suit || 'not chosen yet'}</p>

          <h3>Players in room:</h3>
          <ul>
            {Object.entries(gameState.players || {}).map(([role, name]) => (
              <li key={role}>{role}: {name}</li>
            ))}
          </ul>

          {gameState.phase === 'playing' && (
            <p>{isMyTurn ? "👉 It's YOUR turn" : `Waiting for ${gameState.whose_turn}...`}</p>
          )}

          {gameState.phase === 'choosing_trump' && myRole === 'trump_chooser' && (
            <div>
              <h3>Choose trump:</h3>
              {SUITS.map((suit) => (
                <button key={suit} onClick={() => handleChooseTrump(suit)}>{suit}</button>
              ))}
            </div>
          )}

          <h3>Current trick:</h3>
          <ul>
            {gameState.current_trick?.map((card, index) => (
              <li key={index}>{card.rank} of {card.suit}</li>
            ))}
          </ul>

          <h3>Your hand ({myRole}):</h3>
          <ul>
            {gameState.hands?.[myRole]?.map((card, index) => (
              <li key={index}>
                {gameState.phase === 'playing' && isMyTurn ? (
                  <button onClick={() => handlePlayCard(card)}>{card.rank} of {card.suit}</button>
                ) : (
                  <span>{card.rank} of {card.suit}</span>
                )}
              </li>
            ))}
          </ul>

          <h3>Tricks won:</h3>
          <p>Dealer: {gameState.tricks_won?.dealer} | Trump chooser: {gameState.tricks_won?.trump_chooser} | Third player: {gameState.tricks_won?.third_player}</p>
        </div>
      )}
    </div>
  )
}

export default App