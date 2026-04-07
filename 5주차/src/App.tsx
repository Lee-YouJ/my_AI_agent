import { useEffect, useMemo, useState } from 'react'
import dayjs, { Dayjs } from 'dayjs'
import {
  AppBar,
  Box,
  Button,
  Card,
  CardContent,
  Container,
  Dialog,
  DialogActions,
  DialogContent,
  DialogTitle,
  Divider,
  FormControl,
  IconButton,
  InputLabel,
  List,
  ListItem,
  ListItemText,
  MenuItem,
  Select,
  Stack,
  TextField,
  Toolbar,
  Typography,
} from '@mui/material'
import AddIcon from '@mui/icons-material/Add'
import DeleteIcon from '@mui/icons-material/Delete'
import PersonAddAlt1Icon from '@mui/icons-material/PersonAddAlt1'
import { DateTimePicker } from '@mui/x-date-pickers/DateTimePicker'

type Todo = {
  id: string
  title: string
  dueAtIso: string // ISO string (includes time)
  createdAtIso: string
  // Extension point: priority can be added later
}

type User = {
  id: string
  name: string
  todos: Todo[]
}

type PersistedState = {
  version: 1
  users: User[]
  activeUserId: string | null
}

const STORAGE_KEY = 'todo-mui:v1'

function safeParse(json: string | null): PersistedState | null {
  if (!json) return null
  try {
    return JSON.parse(json) as PersistedState
  } catch {
    return null
  }
}

function newId() {
  return globalThis.crypto?.randomUUID?.() ?? `${Date.now()}-${Math.random().toString(16).slice(2)}`
}

function formatDue(iso: string) {
  const d = dayjs(iso)
  return d.isValid() ? d.format('YYYY-MM-DD HH:mm') : iso
}

function App() {
  const [state, setState] = useState<PersistedState>(() => {
    const parsed = safeParse(localStorage.getItem(STORAGE_KEY))
    if (parsed?.version === 1) return parsed
    return { version: 1, users: [], activeUserId: null }
  })

  const [newUserName, setNewUserName] = useState('')

  const [addOpen, setAddOpen] = useState(false)
  const [newTodoTitle, setNewTodoTitle] = useState('')
  const [newTodoDueAt, setNewTodoDueAt] = useState<Dayjs | null>(dayjs().add(1, 'hour'))

  const [pastAlertOpen, setPastAlertOpen] = useState(false)

  useEffect(() => {
    localStorage.setItem(STORAGE_KEY, JSON.stringify(state))
  }, [state])

  const activeUser = useMemo(() => {
    if (!state.activeUserId) return null
    return state.users.find((u) => u.id === state.activeUserId) ?? null
  }, [state.activeUserId, state.users])

  const sortedTodos = useMemo(() => {
    const todos = activeUser?.todos ?? []
    return [...todos].sort((a, b) => dayjs(a.dueAtIso).valueOf() - dayjs(b.dueAtIso).valueOf())
  }, [activeUser?.todos])

  const ensureActiveUser = () => {
    if (state.activeUserId) return
    if (state.users.length > 0) {
      setState((s) => ({ ...s, activeUserId: s.users[0]!.id }))
      return
    }
    const id = newId()
    const user: User = { id, name: '사용자 1', todos: [] }
    setState({ version: 1, users: [user], activeUserId: id })
  }

  useEffect(() => {
    ensureActiveUser()
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [])

  const addUser = () => {
    const name = newUserName.trim()
    if (!name) return
    const id = newId()
    const user: User = { id, name, todos: [] }
    setState((s) => ({
      ...s,
      users: [...s.users, user],
      activeUserId: s.activeUserId ?? id,
    }))
    setNewUserName('')
  }

  const deleteTodo = (todoId: string) => {
    if (!activeUser) return
    setState((s) => ({
      ...s,
      users: s.users.map((u) =>
        u.id === activeUser.id ? { ...u, todos: u.todos.filter((t) => t.id !== todoId) } : u,
      ),
    }))
  }

  const openAddDialog = () => {
    if (!activeUser) return
    setNewTodoTitle('')
    setNewTodoDueAt(dayjs().add(1, 'hour'))
    setAddOpen(true)
  }

  const submitAddTodo = () => {
    if (!activeUser) return
    const title = newTodoTitle.trim()
    if (!title) return
    if (!newTodoDueAt || !newTodoDueAt.isValid()) return

    const due = newTodoDueAt
    if (due.isBefore(dayjs())) {
      setPastAlertOpen(true)
      return
    }

    const todo: Todo = {
      id: newId(),
      title,
      dueAtIso: due.toISOString(),
      createdAtIso: new Date().toISOString(),
    }

    setState((s) => ({
      ...s,
      users: s.users.map((u) => (u.id === activeUser.id ? { ...u, todos: [...u.todos, todo] } : u)),
    }))
    setAddOpen(false)
  }

  return (
    <Box sx={{ minHeight: '100vh', bgcolor: 'grey.50' }}>
      <AppBar position="sticky" elevation={0} color="default">
        <Toolbar sx={{ gap: 2 }}>
          <Typography variant="h6" sx={{ fontWeight: 700 }}>
            Todo List (마감일/시간)
          </Typography>
          <Box sx={{ flex: 1 }} />

          <FormControl size="small" sx={{ minWidth: 200 }}>
            <InputLabel id="user-select-label">사용자</InputLabel>
            <Select
              labelId="user-select-label"
              label="사용자"
              value={state.activeUserId ?? ''}
              onChange={(e) => setState((s) => ({ ...s, activeUserId: String(e.target.value) }))}
            >
              {state.users.map((u) => (
                <MenuItem key={u.id} value={u.id}>
                  {u.name}
                </MenuItem>
              ))}
            </Select>
          </FormControl>
        </Toolbar>
      </AppBar>

      <Container maxWidth="md" sx={{ py: 3 }}>
        <Stack spacing={2}>
          <Card variant="outlined">
            <CardContent>
              <Typography variant="subtitle1" sx={{ fontWeight: 700, mb: 1 }}>
                사용자 추가 (여러 명 동시 사용)
              </Typography>
              <Stack direction={{ xs: 'column', sm: 'row' }} spacing={1} alignItems="stretch">
                <TextField
                  label="사용자 이름"
                  value={newUserName}
                  onChange={(e) => setNewUserName(e.target.value)}
                  onKeyDown={(e) => {
                    if (e.key === 'Enter') addUser()
                  }}
                  fullWidth
                />
                <Button
                  variant="contained"
                  startIcon={<PersonAddAlt1Icon />}
                  onClick={addUser}
                  sx={{ whiteSpace: 'nowrap' }}
                >
                  추가
                </Button>
              </Stack>
              <Typography variant="caption" color="text.secondary" sx={{ display: 'block', mt: 1 }}>
                새로고침해도 데이터는 로컬 스토리지에 저장됩니다.
              </Typography>
            </CardContent>
          </Card>

          <Card variant="outlined">
            <CardContent>
              <Stack direction="row" alignItems="center" justifyContent="space-between" spacing={2}>
                <Box>
                  <Typography variant="subtitle1" sx={{ fontWeight: 700 }}>
                    메인 화면 (가까운 날짜부터)
                  </Typography>
                  <Typography variant="body2" color="text.secondary">
                    {activeUser ? `현재 사용자: ${activeUser.name}` : '사용자를 선택/추가해 주세요.'}
                  </Typography>
                </Box>

                <Button
                  size="large"
                  variant="contained"
                  startIcon={<AddIcon />}
                  onClick={openAddDialog}
                  disabled={!activeUser}
                  sx={{
                    px: 3,
                    py: 1.5,
                    fontWeight: 800,
                    borderRadius: 3,
                  }}
                >
                  할 일 추가
                </Button>
              </Stack>

              <Divider sx={{ my: 2 }} />

              {sortedTodos.length === 0 ? (
                <Typography variant="body2" color="text.secondary">
                  아직 할 일이 없습니다. 오른쪽의 “할 일 추가” 버튼으로 추가해 보세요.
                </Typography>
              ) : (
                <List disablePadding>
                  {sortedTodos.map((t) => (
                    <ListItem
                      key={t.id}
                      divider
                      secondaryAction={
                        <IconButton edge="end" aria-label="delete" onClick={() => deleteTodo(t.id)}>
                          <DeleteIcon />
                        </IconButton>
                      }
                    >
                      <ListItemText
                        primary={t.title}
                        secondary={`마감: ${formatDue(t.dueAtIso)}`}
                        primaryTypographyProps={{ sx: { fontWeight: 600 } }}
                      />
                    </ListItem>
                  ))}
                </List>
              )}
            </CardContent>
          </Card>
        </Stack>
      </Container>

      <Dialog open={addOpen} onClose={() => setAddOpen(false)} fullWidth maxWidth="sm">
        <DialogTitle>할 일 추가</DialogTitle>
        <DialogContent>
          <Stack spacing={2} sx={{ mt: 1 }}>
            <TextField
              label="할 일"
              value={newTodoTitle}
              onChange={(e) => setNewTodoTitle(e.target.value)}
              autoFocus
              fullWidth
            />
            <DateTimePicker
              label="마감일 (시간 포함)"
              value={newTodoDueAt}
              onChange={(v) => setNewTodoDueAt(v)}
              disablePast={false}
            />
            <Typography variant="caption" color="text.secondary">
              과거 날짜를 선택하면 저장 시 알림이 뜨고 추가가 막힙니다.
            </Typography>
          </Stack>
        </DialogContent>
        <DialogActions>
          <Button onClick={() => setAddOpen(false)}>취소</Button>
          <Button variant="contained" onClick={submitAddTodo}>
            저장
          </Button>
        </DialogActions>
      </Dialog>

      <Dialog open={pastAlertOpen} onClose={() => setPastAlertOpen(false)}>
        <DialogTitle>과거 날짜는 선택할 수 없어요</DialogTitle>
        <DialogContent>
          <Typography variant="body2">
            마감일은 현재 시각 이후로 설정해 주세요.
          </Typography>
        </DialogContent>
        <DialogActions>
          <Button variant="contained" onClick={() => setPastAlertOpen(false)}>
            확인
          </Button>
        </DialogActions>
      </Dialog>
    </Box>
  )
}

export default App
