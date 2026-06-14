const state = {
    incidents: [],
    dashboard: null,
};

const views = {
    dashboard: document.querySelector("#dashboardView"),
    report: document.querySelector("#reportView"),
    register: document.querySelector("#registerView"),
};

const viewTitles = {
    dashboard: "Operational Dashboard",
    report: "Report Incident",
    register: "Incident Register",
};

const titleEl = document.querySelector("#viewTitle");
const searchInput = document.querySelector("#searchInput");
const statusFilter = document.querySelector("#statusFilter");
const dialog = document.querySelector("#incidentDialog");
const detailEl = document.querySelector("#incidentDetail");
const formMessage = document.querySelector("#formMessage");

function titleCase(value) {
    return value.replaceAll("_", " ").replace(/\b\w/g, (letter) => letter.toUpperCase());
}

function formatDate(value) {
    return new Intl.DateTimeFormat("en-GB", {
        dateStyle: "medium",
        timeStyle: "short",
    }).format(new Date(value));
}

async function api(path, options = {}) {
    const response = await fetch(path, {
        headers: { "Content-Type": "application/json" },
        ...options,
    });

    if (!response.ok) {
        const error = await response.json().catch(() => ({ detail: "Request failed" }));
        throw new Error(error.detail || "Request failed");
    }

    return response.json();
}

async function loadDashboard() {
    state.dashboard = await api("/api/dashboard");
    document.querySelector("#totalIncidents").textContent = state.dashboard.total_incidents;
    document.querySelector("#openIncidents").textContent = state.dashboard.open_incidents;
    document.querySelector("#criticalIncidents").textContent = state.dashboard.critical_incidents;
    document.querySelector("#overdueActions").textContent = state.dashboard.overdue_actions;
    renderStatusBreakdown();
}

async function loadIncidents() {
    const params = new URLSearchParams();
    if (statusFilter.value) params.set("status", statusFilter.value);
    if (searchInput.value.trim()) params.set("search", searchInput.value.trim());
    const data = await api(`/api/incidents?${params.toString()}`);
    state.incidents = data.incidents;
    renderIncidentList(document.querySelector("#recentIncidents"), state.incidents.slice(0, 4));
    renderIncidentList(document.querySelector("#incidentRegister"), state.incidents);
}

function renderStatusBreakdown() {
    const container = document.querySelector("#statusBreakdown");
    const rows = state.dashboard.by_status;
    const max = Math.max(...rows.map((row) => row.total), 1);
    container.innerHTML = rows.map((row) => `
        <div class="breakdown-row">
            <strong>${titleCase(row.status)}</strong>
            <div class="bar"><span style="width: ${(row.total / max) * 100}%"></span></div>
            <span>${row.total}</span>
        </div>
    `).join("");
}

function renderIncidentList(container, incidents) {
    if (!incidents.length) {
        container.innerHTML = `<article class="incident-card"><p>No incidents match the current filters.</p></article>`;
        return;
    }

    container.innerHTML = incidents.map((incident) => `
        <article class="incident-card">
            <div>
                <p class="eyebrow">${incident.reference}</p>
                <h3>${incident.title}</h3>
                <div class="incident-meta">
                    <span class="pill ${incident.severity}">${incident.severity}</span>
                    <span class="pill ${incident.status}">${titleCase(incident.status)}</span>
                    <span class="pill">${titleCase(incident.incident_type)}</span>
                    <span class="pill">${incident.location}</span>
                    <span class="pill">${incident.open_action_count || 0} open actions</span>
                </div>
            </div>
            <button class="small-btn" data-incident-id="${incident.id}">Open</button>
        </article>
    `).join("");
}

function showView(name) {
    Object.entries(views).forEach(([key, element]) => {
        element.classList.toggle("is-hidden", key !== name);
    });
    document.querySelectorAll(".nav-item").forEach((item) => {
        item.classList.toggle("is-active", item.dataset.view === name);
    });
    titleEl.textContent = viewTitles[name];
}

async function openIncident(incidentId) {
    const incident = await api(`/api/incidents/${incidentId}`);
    detailEl.innerHTML = `
        <p class="eyebrow">${incident.reference}</p>
        <h2>${incident.title}</h2>
        <div class="incident-meta">
            <span class="pill ${incident.severity}">${incident.severity}</span>
            <span class="pill ${incident.status}">${titleCase(incident.status)}</span>
            <span class="pill">${titleCase(incident.incident_type)}</span>
        </div>
        <div class="detail-grid">
            <div class="detail-box"><span>Location</span><strong>${incident.location}</strong></div>
            <div class="detail-box"><span>Reported by</span><strong>${incident.reported_by}</strong></div>
            <div class="detail-box"><span>Assigned to</span><strong>${incident.assigned_to || "Unassigned"}</strong></div>
            <div class="detail-box"><span>Occurred</span><strong>${formatDate(incident.occurred_at)}</strong></div>
        </div>
        <div class="detail-box">
            <span>Description</span>
            <p>${incident.description}</p>
        </div>
        <div class="detail-box">
            <span>Immediate action</span>
            <p>${incident.immediate_action || "No immediate action recorded."}</p>
        </div>
        <h3>Corrective Actions</h3>
        <div class="action-list">
            ${incident.corrective_actions.length ? incident.corrective_actions.map((action) => `
                <div class="action-item">
                    <strong>${action.action}</strong>
                    <p>Owner: ${action.owner} | Due: ${action.due_date} | Status: ${titleCase(action.status)}</p>
                </div>
            `).join("") : "<p>No corrective actions added yet.</p>"}
        </div>
    `;
    dialog.showModal();
}

async function refresh() {
    await Promise.all([loadDashboard(), loadIncidents()]);
}

document.querySelectorAll("[data-view]").forEach((button) => {
    button.addEventListener("click", () => showView(button.dataset.view));
});

document.body.addEventListener("click", (event) => {
    const button = event.target.closest("[data-incident-id]");
    if (button) openIncident(button.dataset.incidentId);
});

searchInput.addEventListener("input", loadIncidents);
statusFilter.addEventListener("change", loadIncidents);

document.querySelector("#incidentForm").addEventListener("submit", async (event) => {
    event.preventDefault();
    const form = event.currentTarget;
    const submitButton = form.querySelector("button[type='submit']");
    formMessage.textContent = "Saving report...";
    formMessage.className = "form-message";
    submitButton.disabled = true;

    const formData = new FormData(form);
    const payload = Object.fromEntries(formData.entries());
    payload.occurred_at = new Date(payload.occurred_at).toISOString();

    try {
        await api("/api/incidents", {
            method: "POST",
            body: JSON.stringify(payload),
        });

        form.reset();
        document.querySelector("input[name='occurred_at']").value = new Date().toISOString().slice(0, 16);
        formMessage.textContent = "Report saved and added to the register.";
        formMessage.classList.add("success");
        await refresh();
        showView("register");
    } catch (error) {
        formMessage.textContent = error.message;
        formMessage.classList.add("error");
    } finally {
        submitButton.disabled = false;
    }
});

document.querySelector("input[name='occurred_at']").value = new Date().toISOString().slice(0, 16);
refresh();
