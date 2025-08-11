import { StrictMode } from 'react'
import { createRoot } from 'react-dom/client'
import { QueryClient, QueryClientProvider, useQuery } from '@tanstack/react-query'
import { BrowserRouter, Route, Routes, Link } from 'react-router-dom'

const qc = new QueryClient()

function Home() {
  const { data } = useQuery({
    queryKey: ['health'],
    queryFn: async () => {
      const res = await fetch('/api/v1/health')
      if (!res.ok) throw new Error('Health failed')
      return res.json()
    },
  })
  return (
    <div style={{ padding: 16 }}>
      <h1>Simple ABX (React)</h1>
      <p>API health: {data?.status ?? '...'}</p>
      <nav>
        <Link to="/">Home</Link>
      </nav>
    </div>
  )
}

createRoot(document.getElementById('root')!).render(
  <StrictMode>
    <QueryClientProvider client={qc}>
      <BrowserRouter>
        <Routes>
          <Route path="/" element={<Home />} />
        </Routes>
      </BrowserRouter>
    </QueryClientProvider>
  </StrictMode>
)
