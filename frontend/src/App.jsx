import { useState, useEffect, useRef } from 'react'
import './App.css'

const SUITS = ['Hearts', 'Diamonds', 'Clubs', 'Spades']
const SUIT_SYMBOLS = { Hearts: '♥', Diamonds: '♦', Clubs: '♣', Spades: '♠' }
const RED_SUITS = ['Hearts', 'Diamonds']
const BACKEND_HTTP = import.meta.env.VITE_BACKEND_HTTP || 'http://127.0.0.1:8000'
const BACKEND_WS = import.meta.env.VITE_BACKEND_WS || 'ws://127.0.0.1:8000'

// A single playing card, drawn with CSS — no image files needed
function PlayingCard({ card }) {
  const isRed = RED_SUITS.includes(card.suit)
  return (
    <div className={`card ${isRed ? '' : ''}`}>
      <span className="rank" style={{ color: isRed ? 'var(--red)' : 'var(--ink)' }}>
        {card.rank}
      </span>
      <span className={`suit ${isRed ? 'suit-red' : 'suit-black'}`}>
        {SUIT_SYMBOLS[card.suit]}
      </span>
    </div>
  )
}

function App() {
  const [screen, setScreen] = useState('landing')
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

    ws.onopen = () => setConnected(true)

    ws.onmessage = (event) => {
      const data = JSON.parse(event.data)
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
    wsRef.current.send(JSON.stringify({ type: 'choose_trump', suit }))
  }

  const handlePlayCard = (card) => {
    wsRef.current.send(JSON.stringify({ type: 'play_card', card }))
  }

  if (screen === 'landing') {
    return (
      <div className="App">
        <div className="landing">
          <h1>3-2-5</h1>
          {errorMessage && <div className="error-banner">⚠️ {errorMessage}</div>}
          <div className="landing-panel">
            <div className="field">
              <label>Your name</label>
              <input
                type="text"
                value={playerName}
                onChange={(e) => setPlayerName(e.target.value)}
                placeholder="e.g. Aditya"
              />
            </div>
            <button className="btn-primary" onClick={handleCreateRoom}>
              Create Room
            </button>
            <div className="divider">or join with a code</div>
            <div className="join-row">
              <input
                type="text"
                placeholder="ROOM CODE"
                value={joinCodeInput}
                onChange={(e) => setJoinCodeInput(e.target.value)}
              />
              <button className="btn-secondary" onClick={handleJoinRoom}>
                Join
              </button>
            </div>
          </div>
        </div>
      </div>
    )
  }

  const isMyTurn = gameState?.whose_turn === myRole

  return (
    <div className="App">
      <div className="top-bar">
        <span className="room-code-pill">{roomCode}</span>
        <span className="status-line">
          Trump: <strong>{gameState?.trump_suit || '—'}</strong>
          {'  ·  '}
          Phase: <strong>{gameState?.phase}</strong>
        </span>
      </div>

      {errorMessage && <div className="error-banner">⚠️ {errorMessage}</div>}

      {gameState && myRole && (
        <>
          <div className="players-row">
            {Object.keys(gameState.quotas || {}).map((role) => (
              <div
                key={role}
                className={`player-badge ${gameState.whose_turn === role ? 'active-turn' : ''}`}
              >
                <div className="role">{role.replace('_', ' ')}</div>
                <div className="name">{gameState.players?.[role] || '...'}</div>
                <div className="quota">
                  {gameState.quotas[role]} of {gameState.tricks_won[role]}
                </div>
              </div>
            ))}
          </div>

          {gameState.phase === 'playing' && (
            <div className="turn-banner">
              {isMyTurn ? "👉 It's your turn" : `Waiting for ${gameState.players?.[gameState.whose_turn]}...`}
            </div>
          )}

          {gameState.phase === 'choosing_trump' && myRole === 'trump_chooser' && (
            <div className="trump-select">
              <h3>Choose trump</h3>
              <div className="suit-buttons">
                {SUITS.map((suit) => (
                  <button
                    key={suit}
                    className={`suit-btn ${RED_SUITS.includes(suit) ? 'suit-red' : 'suit-black'}`}
                    onClick={() => handleChooseTrump(suit)}
                  >
                    {SUIT_SYMBOLS[suit]}
                  </button>
                ))}
              </div>
            </div>
          )}

          <div className="table-area">
            {gameState.current_trick?.length > 0 ? (
              gameState.current_trick.map((card, i) => <PlayingCard key={i} card={card} />)
            ) : (
              <span className="empty-hint">No cards played yet this trick</span>
            )}
          </div>

          <div className="hand-section">
            <h3>Your hand</h3>
            <div className="hand-row">
              {gameState.hands?.[myRole]?.map((card, i) => {
                const clickable = gameState.phase === 'playing' && isMyTurn
                return clickable ? (
                  <button key={i} className="card-btn" onClick={() => handlePlayCard(card)}>
                    <PlayingCard card={card} />
                  </button>
                ) : (
                  <div key={i} className="card disabled" style={{ display: 'contents' }}>
                    <PlayingCard card={card} />
                  </div>
                )
              })}
            </div>
          </div>

          {gameState.phase === 'hand_complete' && (
            <div className="results-panel">
              <h2>Hand Complete</h2>
              <table className="results-table">
                <thead>
                  <tr>
                    <th>Player</th>
                    <th>Needed</th>
                    <th>Made</th>
                    <th>Result</th>
                  </tr>
                </thead>
                <tbody>
                  {Object.keys(gameState.quotas || {}).map((role) => (
                    <tr key={role}>
                      <td>{gameState.players?.[role]}</td>
                      <td>{gameState.quotas[role]}</td>
                      <td>{gameState.tricks_won[role]}</td>
                      <td>{gameState.quota_results?.[role] ? '✅' : '❌'}</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          )}
        </>
      )}
    </div>
  )
}

export default App