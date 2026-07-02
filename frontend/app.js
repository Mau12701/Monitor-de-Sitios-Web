let autoRefreshInterval = null

function colorPing(ms) {
  if (!ms) return ''
  if (ms < 300) return 'ping-fast'
  if (ms < 800) return 'ping-mid'
  return 'ping-slow'
}

function uptimeColor(pct) {
  if (pct >= 95) return ''
  if (pct >= 80) return 'mid'
  return 'low'
}

async function cargarSitios() {
  try {
    const res = await fetch('/api/sitios')
    const sitios = await res.json()
    renderTabla(sitios)
    actualizarStats(sitios)
  } catch (e) {
    console.error('Error cargando sitios:', e)
  }
}

function renderTabla(sitios) {
  const tbody = document.getElementById('tabla-body')
  document.getElementById('badge-total').textContent = sitios.length
  document.getElementById('stat-total').textContent = sitios.length

  if (sitios.length === 0) {
    tbody.innerHTML = '<tr><td colspan="7" class="empty-msg">No hay sitios registrados. Agrega uno abajo.</td></tr>'
    return
  }

  tbody.innerHTML = sitios.map(s => {
    const ultimo = s.ultimo_chequeo
    const online = ultimo ? ultimo.online : null
    const ping = ultimo ? ultimo.tiempo_ms : null
    const code = ultimo ? ultimo.status_code : null
    const error = ultimo ? ultimo.error : null

    const dotClass = online === null ? 'dot-pending' : online ? 'dot-online' : 'dot-offline'
    const estadoTexto = online === null ? 'Pendiente' : online ? 'Online' : 'Offline'
    const pingTexto = ping ? `<span class="${colorPing(ping)}">${ping} ms</span>` : (error || '---')
    const codeTexto = code ? code : '---'
    const uptime = s.uptime ?? 100
    const uptimeClass = uptimeColor(uptime)

    return `
      <tr>
        <td><span class="dot ${dotClass}"></span>${estadoTexto}</td>
        <td>${s.nombre}</td>
        <td style="color: var(--text2)">${s.url}</td>
        <td>${codeTexto}</td>
        <td>${pingTexto}</td>
        <td>
          <div class="uptime-bar"><div class="uptime-fill ${uptimeClass}" style="width:${uptime}%"></div></div>
          ${uptime}%
        </td>
        <td>
          <button class="btn-del" onclick="eliminarSitio(${s.id})">✕ Eliminar</button>
        </td>
      </tr>
    `
  }).join('')
}

function actualizarStats(sitios) {
  const online = sitios.filter(s => s.ultimo_chequeo?.online).length
  const offline = sitios.filter(s => s.ultimo_chequeo && !s.ultimo_chequeo.online).length
  const pings = sitios.map(s => s.ultimo_chequeo?.tiempo_ms).filter(Boolean)
  const promedio = pings.length ? Math.round(pings.reduce((a, b) => a + b, 0) / pings.length) : 0

  document.getElementById('stat-online').textContent = online
  document.getElementById('stat-offline').textContent = offline
  document.getElementById('stat-promedio').textContent = promedio ? `${promedio} ms` : '--- ms'
  document.getElementById('sidebar-online').textContent = `${online} / ${sitios.length}`
}

async function chequearTodos() {
  const btn = document.getElementById('btn-chequear')
  const estado = document.getElementById('estado-chequeo')

  btn.disabled = true
  btn.textContent = 'Chequeando...'
  estado.classList.remove('oculto')

  try {
    await fetch('/api/chequear', { method: 'POST' })
    await cargarSitios()
    const ahora = new Date().toLocaleTimeString('es-MX')
    document.getElementById('sidebar-tiempo').textContent = ahora
  } catch (e) {
    console.error('Error chequeando:', e)
  } finally {
    btn.disabled = false
    btn.textContent = '⟳ Chequear todos'
    estado.classList.add('oculto')
  }
}

async function agregarSitio() {
  const nombre = document.getElementById('input-nombre').value.trim()
  const url = document.getElementById('input-url').value.trim()
  const msg = document.getElementById('msg-agregar')

  if (!url) {
    msg.textContent = 'La URL es obligatoria'
    msg.className = 'msg-form msg-err'
    return
  }

  try {
    const res = await fetch('/api/sitios', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ url, nombre })
    })
    const data = await res.json()

    if (res.ok) {
      msg.textContent = `✓ ${data.mensaje}`
      msg.className = 'msg-form msg-ok'
      document.getElementById('input-nombre').value = ''
      document.getElementById('input-url').value = ''
      await cargarSitios()
    } else {
      msg.textContent = `✗ ${data.detail}`
      msg.className = 'msg-form msg-err'
    }
  } catch (e) {
    msg.textContent = 'Error al conectar con el servidor'
    msg.className = 'msg-form msg-err'
  }
}

async function eliminarSitio(id) {
  if (!confirm('¿Eliminar este sitio y su historial?')) return
  await fetch(`/api/sitios/${id}`, { method: 'DELETE' })
  await cargarSitios()
}

// Auto-refresh cada 60 segundos
function iniciarAutoRefresh() {
  autoRefreshInterval = setInterval(() => {
    chequearTodos()
  }, 60000)
}

// Iniciar
cargarSitios()
iniciarAutoRefresh()