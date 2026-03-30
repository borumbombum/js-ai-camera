async function fetchEvents() {
    const list = document.getElementById('events-list');
    try {
        const response = await fetch('/events');
        const data = await response.json();
        const events = data.events || [];
        
        if (events.length === 0) {
            list.innerHTML = '<p class="text-base-content/50 text-sm">No events recorded</p>';
        } else {
            list.innerHTML = events.map(event => {
                const date = new Date(event.timestamp);
                const timeStr = date.toLocaleString();
                const eventDate = date.toISOString().split('T')[0];
                const hasScreenshot = event.screenshot_path && event.timelapse_url;
                const timelapseHref = hasScreenshot ? event.timelapse_url : `/timelapse?date=${eventDate}`;
                const imageIndicator = hasScreenshot ? '' : '<span class="text-xs text-error">(image deleted)</span>';
                return `
                    <a href="${timelapseHref}" class="block bg-base-300 rounded-lg p-3 space-y-1 hover:bg-base-100 transition-colors cursor-pointer ${!hasScreenshot ? 'opacity-60' : ''}">
                        <div class="flex justify-between items-start">
                            <span class="text-xs text-base-content/60">${timeStr}</span>
                            <button onclick="event.preventDefault(); event.stopPropagation(); deleteEvent(${event.id})" class="btn btn-xs btn-circle btn-error">✕</button>
                        </div>
                        <p class="text-sm font-medium">${event.objects}</p>
                        ${imageIndicator}
                    </a>
                `;
            }).join('');
        }
        
        document.getElementById('events-drawer-toggle').checked = true;
    } catch (err) {
        list.innerHTML = `<p class="text-error text-sm">Failed to load events: ${err.message}</p>`;
        document.getElementById('events-drawer-toggle').checked = true;
    }
}

async function deleteEvent(eventId) {
    if (!confirm('Delete this event?')) return;
    try {
        await fetch(`/events/${eventId}`, { method: 'DELETE' });
        fetchEvents();
    } catch (err) {
        console.error('Failed to delete event:', err);
    }
}

function showEventsDrawer() {
    fetchEvents();
    const sidebarDrawer = document.getElementById('sidebar-drawer');
    if (sidebarDrawer) sidebarDrawer.checked = false;
    document.getElementById('events-drawer-toggle').checked = true;
}

async function fetchLogs() {
    const container = document.getElementById('logs-container');
    try {
        const response = await fetch('/logs');
        const data = await response.json();
        
        if (data.logs.length === 0) {
            container.innerHTML = '<p class="text-base-content/50">No logs yet</p>';
        } else {
            container.innerHTML = data.logs.map(log => {
                let levelColor = 'text-info';
                if (log.level === 'WARNING') levelColor = 'text-warning';
                if (log.level === 'ERROR') levelColor = 'text-error';
                return `<div><span class="text-base-content/50">${log.timestamp}</span> <span class="${levelColor}">[${log.level}]</span> ${log.message}</div>`;
            }).reverse().join('');
        }
        
        document.getElementById('logs_modal').showModal();
    } catch (err) {
        container.innerHTML = `<p class="text-error">Failed to load logs</p>`;
        document.getElementById('logs_modal').showModal();
    }
}
