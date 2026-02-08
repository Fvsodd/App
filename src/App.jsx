import { useMemo, useState } from 'react'
import {
  AppBar,
  Box,
  Button,
  Card,
  CardContent,
  Chip,
  Container,
  Dialog,
  DialogActions,
  DialogContent,
  DialogTitle,
  Divider,
  Drawer,
  FormControl,
  Grid,
  InputLabel,
  List,
  ListItemButton,
  ListItemIcon,
  ListItemText,
  MenuItem,
  Paper,
  Select,
  Stack,
  Tab,
  Tabs,
  TextField,
  Toolbar,
  Typography,
} from '@mui/material'
import AppsIcon from '@mui/icons-material/Apps'
import PsychologyIcon from '@mui/icons-material/Psychology'
import DashboardIcon from '@mui/icons-material/Dashboard'
import AdminPanelSettingsIcon from '@mui/icons-material/AdminPanelSettings'
import UploadFileIcon from '@mui/icons-material/UploadFile'
import PersonIcon from '@mui/icons-material/Person'

const categories = ['education', 'programming', 'design', 'ai tools', 'utilities']

const seedUsers = [
  { id: 1, username: 'student1', password: 'pass123', role: 'student', faculty: 'IT', course: 2 },
  { id: 2, username: 'student2', password: 'pass123', role: 'student', faculty: 'Architecture', course: 3 },
  { id: 3, username: 'teacher1', password: 'pass123', role: 'teacher', faculty: 'IT' },
  { id: 4, username: 'admin1', password: 'admin123', role: 'admin', faculty: 'Administration' },
]

const seedApps = [
  { id: 1, name: 'Python Lab Assistant', description: 'Interactive programming helper for first-year coding courses.', category: 'programming', authorId: 1, author: 'student1', downloads: 32, status: 'approved' },
  { id: 2, name: 'Arch Sketch Toolkit', description: 'Tools for architecture concept sketches and quick annotations.', category: 'design', authorId: 2, author: 'student2', downloads: 18, status: 'approved' },
  { id: 3, name: 'AI Report Summarizer', description: 'Summarize long educational reports and articles using AI prompts.', category: 'ai tools', authorId: 1, author: 'student1', downloads: 26, status: 'approved' },
  { id: 4, name: 'Campus Planner', description: 'Simple utility to plan study schedule and deadlines.', category: 'utilities', authorId: 2, author: 'student2', downloads: 40, status: 'approved' },
]

const token = (text) => text.toLowerCase().split(/\s+/).map((w) => w.replace(/[^\w]/g, '')).filter(Boolean)

const semanticScore = (query, text) => {
  const synonyms = {
    architecture: ['design', 'sketch', 'modeling', 'cad'],
    project: ['assignment', 'course', 'task'],
    ai: ['ml', 'machine', 'intelligence'],
    coding: ['programming', 'python', 'developer'],
    study: ['education', 'learning', 'course'],
  }
  const q = token(query)
  const expanded = q.flatMap((t) => [t, ...(synonyms[t] || [])])
  const t = token(text)
  const overlap = expanded.filter((x) => t.includes(x)).length
  return expanded.length ? overlap / expanded.length : 0
}

function Login({ onLogin }) {
  const [username, setUsername] = useState('student1')
  const [password, setPassword] = useState('pass123')
  const [error, setError] = useState('')

  const submit = () => {
    const found = seedUsers.find((u) => u.username === username && u.password === password)
    if (!found) return setError('Invalid credentials')
    onLogin(found)
  }

  return (
    <Container maxWidth="sm" sx={{ mt: 10 }}>
      <Card>
        <CardContent sx={{ p: 4 }}>
          <Typography variant="h4" gutterBottom>Zhetisu University AI Marketplace</Typography>
          <Typography color="text.secondary" sx={{ mb: 3 }}>Beta desktop demo interface for administration and teachers.</Typography>
          <Stack spacing={2}>
            <TextField label="Username" value={username} onChange={(e) => setUsername(e.target.value)} />
            <TextField type="password" label="Password" value={password} onChange={(e) => setPassword(e.target.value)} />
            <Button variant="contained" size="large" onClick={submit}>Sign In</Button>
            {error && <Typography color="error">{error}</Typography>}
            <Typography variant="body2" color="text.secondary">Demo: student1/pass123, teacher1/pass123, admin1/admin123</Typography>
          </Stack>
        </CardContent>
      </Card>
    </Container>
  )
}

function Marketplace({ user, apps, setApps, installs, setInstalls }) {
  const [search, setSearch] = useState('')
  const [category, setCategory] = useState('all')
  const [selected, setSelected] = useState(null)

  const visibleApps = useMemo(() => {
    const filtered = apps.filter((a) => a.status === 'approved').filter((a) => category === 'all' || a.category === category)
    if (!search.trim()) return filtered.sort((a, b) => b.downloads - a.downloads)
    return filtered
      .map((a) => ({ ...a, score: semanticScore(search, `${a.name} ${a.description} ${a.category}`) }))
      .filter((a) => a.score > 0.08 || `${a.name} ${a.description}`.toLowerCase().includes(search.toLowerCase()))
      .sort((a, b) => b.score - a.score || b.downloads - a.downloads)
  }, [apps, category, search])

  const install = (appId) => {
    if (user.role !== 'student') return
    if (!installs.some((i) => i.userId === user.id && i.appId === appId)) {
      setInstalls([...installs, { userId: user.id, appId }])
    }
    setApps(apps.map((a) => (a.id === appId ? { ...a, downloads: a.downloads + 1 } : a)))
  }

  return (
    <Stack spacing={2}>
      <Paper sx={{ p: 2 }}>
        <Stack direction={{ xs: 'column', md: 'row' }} spacing={2} alignItems="center">
          <TextField fullWidth label="Semantic search" placeholder="e.g. tool for architecture course project" value={search} onChange={(e) => setSearch(e.target.value)} />
          <FormControl sx={{ minWidth: 170 }}>
            <InputLabel>Category</InputLabel>
            <Select value={category} label="Category" onChange={(e) => setCategory(e.target.value)}>
              <MenuItem value="all">all</MenuItem>
              {categories.map((c) => <MenuItem key={c} value={c}>{c}</MenuItem>)}
            </Select>
          </FormControl>
        </Stack>
      </Paper>

      <Grid container spacing={2}>
        <Grid item xs={12} md={7}>
          <Stack spacing={1.5}>
            {visibleApps.map((a) => (
              <Paper key={a.id} sx={{ p: 2, cursor: 'pointer', border: selected?.id === a.id ? '2px solid #1e5aa7' : '1px solid #ddd' }} onClick={() => setSelected(a)}>
                <Stack direction="row" justifyContent="space-between" alignItems="center">
                  <Box>
                    <Typography variant="h6">{a.name}</Typography>
                    <Typography variant="body2" color="text.secondary">{a.description}</Typography>
                  </Box>
                  <Stack alignItems="end">
                    <Chip label={a.category} size="small" />
                    <Typography variant="caption" sx={{ mt: 1 }}>{a.downloads} downloads</Typography>
                  </Stack>
                </Stack>
              </Paper>
            ))}
          </Stack>
        </Grid>
        <Grid item xs={12} md={5}>
          <Paper sx={{ p: 2, minHeight: 250 }}>
            <Typography variant="h6" gutterBottom>Application details</Typography>
            {selected ? (
              <Stack spacing={1}>
                <Typography><b>Name:</b> {selected.name}</Typography>
                <Typography><b>Author:</b> {selected.author}</Typography>
                <Typography><b>Category:</b> {selected.category}</Typography>
                <Typography><b>Description:</b> {selected.description}</Typography>
                <Button variant="contained" onClick={() => install(selected.id)} disabled={user.role !== 'student'}>Install (mock)</Button>
                {user.role !== 'student' && <Typography variant="caption">Install is available only for student accounts in MVP.</Typography>}
              </Stack>
            ) : <Typography color="text.secondary">Select an application to see details.</Typography>}
          </Paper>
        </Grid>
      </Grid>
    </Stack>
  )
}

function AINavigator({ user, apps }) {
  const [faculty, setFaculty] = useState(user.faculty || '')
  const [course, setCourse] = useState(user.course || '')
  const [interests, setInterests] = useState('')
  const [result, setResult] = useState('Press "Generate" to get recommendations.')

  const generate = () => {
    const scored = apps
      .filter((a) => a.status === 'approved')
      .map((a) => ({ ...a, score: semanticScore(`${faculty} ${interests}`, `${a.name} ${a.description} ${a.category}`) + a.downloads / 1000 }))
      .sort((a, b) => b.score - a.score)
      .slice(0, 3)

    let focus = 'programming'
    if (faculty.toLowerCase().includes('arch') || interests.toLowerCase().includes('design')) focus = 'design'
    else if (interests.toLowerCase().includes('ai') || interests.toLowerCase().includes('data')) focus = 'ai tools'

    const idea = {
      programming: 'build a grading assistant plugin that checks code style and gives hints',
      design: 'create an AI-assisted architecture visualization and feedback tool',
      'ai tools': 'develop a local AI note summarizer for university research papers',
    }[focus]

    setResult(
      `You are a ${faculty || 'general'} student (course ${course || 'N/A'}).\n\n` +
      `Install now:\n${scored.map((a) => `- ${a.name} (${a.category})`).join('\n')}\n\n` +
      `Skills to develop:\n- Product thinking\n- Data literacy\n- Practical implementation\n\n` +
      `Portfolio project idea:\n${idea}`
    )
  }

  return (
    <Stack spacing={2}>
      <Paper sx={{ p: 2 }}>
        <Grid container spacing={2}>
          <Grid item xs={12} md={4}><TextField fullWidth label="Faculty" value={faculty} onChange={(e) => setFaculty(e.target.value)} /></Grid>
          <Grid item xs={12} md={2}><TextField fullWidth label="Course" value={course} onChange={(e) => setCourse(e.target.value)} /></Grid>
          <Grid item xs={12} md={6}><TextField fullWidth label="Interests" value={interests} onChange={(e) => setInterests(e.target.value)} placeholder="AI, architecture, productivity" /></Grid>
        </Grid>
        <Button sx={{ mt: 2 }} variant="contained" onClick={generate}>Generate recommendations</Button>
      </Paper>
      <Paper sx={{ p: 2, whiteSpace: 'pre-line' }}>
        <Typography variant="h6" gutterBottom>AI Navigator Output</Typography>
        <Typography>{result}</Typography>
      </Paper>
    </Stack>
  )
}

function Portfolio({ user, apps, installs }) {
  const installed = installs.filter((i) => i.userId === user.id).map((i) => apps.find((a) => a.id === i.appId)).filter(Boolean)
  const published = apps.filter((a) => a.authorId === user.id)
  const totalDownloads = published.reduce((n, a) => n + a.downloads, 0)
  const score = Math.min(100, installed.length * 12 + published.length * 15 + Math.floor(totalDownloads / 3))

  return (
    <Grid container spacing={2}>
      <Grid item xs={12} md={4}><Paper sx={{ p: 2 }}><Typography variant="h6">Profile</Typography><Typography>{user.username}</Typography><Typography color="text.secondary">{user.faculty}</Typography></Paper></Grid>
      <Grid item xs={12} md={4}><Paper sx={{ p: 2 }}><Typography variant="h6">Installed Apps</Typography>{installed.map((a) => <Typography key={a.id}>• {a.name}</Typography>) || <Typography>-</Typography>}</Paper></Grid>
      <Grid item xs={12} md={4}><Paper sx={{ p: 2 }}><Typography variant="h6">Published Apps</Typography>{published.map((a) => <Typography key={a.id}>• {a.name} ({a.status})</Typography>) || <Typography>-</Typography>}</Paper></Grid>
      <Grid item xs={12}><Paper sx={{ p: 2 }}><Typography variant="h6">AI usefulness score: {score}/100</Typography><Typography color="text.secondary">Based on usage, published apps and downloads.</Typography></Paper></Grid>
    </Grid>
  )
}

function TeacherDashboard({ apps, installs }) {
  const topApps = [...apps].filter((a) => a.status === 'approved').sort((a, b) => b.downloads - a.downloads).slice(0, 5)
  return (
    <Grid container spacing={2}>
      <Grid item xs={12} md={6}><Paper sx={{ p: 2 }}><Typography variant="h6">Most used applications</Typography>{topApps.map((a) => <Typography key={a.id}>• {a.name} — {a.downloads} downloads</Typography>)}</Paper></Grid>
      <Grid item xs={12} md={6}><Paper sx={{ p: 2 }}><Typography variant="h6">Usage summary</Typography><Typography>Total installations: {installs.length}</Typography><Typography>Approved apps: {apps.filter((a) => a.status === 'approved').length}</Typography></Paper></Grid>
    </Grid>
  )
}

function AdminPanel({ apps, setApps }) {
  const pending = apps.filter((a) => a.status === 'pending')
  const update = (id, status) => setApps(apps.map((a) => (a.id === id ? { ...a, status } : a)))

  return (
    <Stack spacing={2}>
      <Paper sx={{ p: 2 }}>
        <Typography variant="h6">Moderation queue</Typography>
        <Typography color="text.secondary">Only unfinished controls are hidden for this beta demo.</Typography>
      </Paper>
      {pending.length === 0 ? <Paper sx={{ p: 2 }}><Typography>No pending applications.</Typography></Paper> : pending.map((a) => (
        <Paper key={a.id} sx={{ p: 2 }}>
          <Stack direction={{ xs: 'column', md: 'row' }} justifyContent="space-between" alignItems={{ md: 'center' }} spacing={1}>
            <Box><Typography variant="h6">{a.name}</Typography><Typography color="text.secondary">{a.description}</Typography></Box>
            <Stack direction="row" spacing={1}><Button variant="contained" onClick={() => update(a.id, 'approved')}>Approve</Button><Button color="error" variant="outlined" onClick={() => update(a.id, 'rejected')}>Reject</Button></Stack>
          </Stack>
        </Paper>
      ))}
    </Stack>
  )
}

function UploadApp({ user, apps, setApps }) {
  const [open, setOpen] = useState(false)
  const [form, setForm] = useState({ name: '', category: categories[0], description: '' })

  const submit = () => {
    if (!form.name || !form.description) return
    setApps([...apps, { id: apps.length + 1, name: form.name, category: form.category, description: form.description, authorId: user.id, author: user.username, downloads: 0, status: 'pending' }])
    setOpen(false)
    setForm({ name: '', category: categories[0], description: '' })
  }

  return (
    <>
      <Paper sx={{ p: 2 }}>
        <Typography variant="h6">Student Upload</Typography>
        <Typography color="text.secondary" sx={{ mb: 2 }}>For beta clarity, upload flow is in a guided dialog and advanced fields are hidden.</Typography>
        <Button variant="contained" startIcon={<UploadFileIcon />} onClick={() => setOpen(true)}>Submit new application</Button>
      </Paper>
      <Dialog open={open} onClose={() => setOpen(false)} fullWidth>
        <DialogTitle>Submit Application</DialogTitle>
        <DialogContent>
          <Stack spacing={2} sx={{ mt: 1 }}>
            <TextField label="Application name" value={form.name} onChange={(e) => setForm({ ...form, name: e.target.value })} />
            <FormControl>
              <InputLabel>Category</InputLabel>
              <Select value={form.category} label="Category" onChange={(e) => setForm({ ...form, category: e.target.value })}>
                {categories.map((c) => <MenuItem key={c} value={c}>{c}</MenuItem>)}
              </Select>
            </FormControl>
            <TextField multiline minRows={3} label="Description" value={form.description} onChange={(e) => setForm({ ...form, description: e.target.value })} />
          </Stack>
        </DialogContent>
        <DialogActions>
          <Button onClick={() => setOpen(false)}>Cancel</Button>
          <Button variant="contained" onClick={submit}>Send for approval</Button>
        </DialogActions>
      </Dialog>
    </>
  )
}

export default function App() {
  const [user, setUser] = useState(null)
  const [apps, setApps] = useState(seedApps)
  const [installs, setInstalls] = useState([])
  const [tab, setTab] = useState('marketplace')

  if (!user) return <Login onLogin={setUser} />

  const nav = [
    { key: 'marketplace', label: 'Marketplace', icon: <AppsIcon /> },
    { key: 'ai', label: 'AI Navigator', icon: <PsychologyIcon /> },
    ...(user.role === 'student' ? [{ key: 'upload', label: 'Upload', icon: <UploadFileIcon /> }, { key: 'portfolio', label: 'Portfolio', icon: <PersonIcon /> }] : []),
    ...(user.role === 'teacher' ? [{ key: 'teacher', label: 'Teacher Dashboard', icon: <DashboardIcon /> }] : []),
    ...(user.role === 'admin' ? [{ key: 'admin', label: 'Admin Panel', icon: <AdminPanelSettingsIcon /> }] : []),
  ]

  return (
    <Box sx={{ display: 'flex' }}>
      <AppBar position="fixed" elevation={0} sx={{ zIndex: 1300 }}>
        <Toolbar>
          <Typography sx={{ flexGrow: 1, fontWeight: 700 }}>Zhetisu University AI Marketplace — Beta Demo</Typography>
          <Chip label={`${user.username} (${user.role})`} color="secondary" sx={{ mr: 2 }} />
          <Button color="inherit" onClick={() => { setUser(null); setTab('marketplace') }}>Logout</Button>
        </Toolbar>
      </AppBar>

      <Drawer variant="permanent" sx={{ width: 250, [`& .MuiDrawer-paper`]: { width: 250, boxSizing: 'border-box', mt: 8 } }}>
        <List>
          {nav.map((item) => (
            <ListItemButton key={item.key} selected={tab === item.key} onClick={() => setTab(item.key)}>
              <ListItemIcon>{item.icon}</ListItemIcon>
              <ListItemText primary={item.label} />
            </ListItemButton>
          ))}
        </List>
      </Drawer>

      <Box component="main" sx={{ flexGrow: 1, ml: '250px', mt: 8, p: 3 }}>
        <Paper sx={{ p: 2, mb: 2 }}>
          <Typography variant="h6">What to do on this screen</Typography>
          <Typography color="text.secondary">Use left navigation to switch modules. Start with Marketplace, then AI Navigator. Unfinished advanced settings are intentionally hidden in beta mode.</Typography>
        </Paper>
        {tab === 'marketplace' && <Marketplace user={user} apps={apps} setApps={setApps} installs={installs} setInstalls={setInstalls} />}
        {tab === 'ai' && <AINavigator user={user} apps={apps} />}
        {tab === 'upload' && <UploadApp user={user} apps={apps} setApps={setApps} />}
        {tab === 'portfolio' && <Portfolio user={user} apps={apps} installs={installs} />}
        {tab === 'teacher' && <TeacherDashboard apps={apps} installs={installs} />}
        {tab === 'admin' && <AdminPanel apps={apps} setApps={setApps} />}
      </Box>
    </Box>
  )
}
