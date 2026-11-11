// The wizard uses the same Lovelace configuration flow as Pellet Tracker.
const devicePath = /^\/config\/devices\/device\/([^/]+)\/?$/;
const isEditable = view => !view.strategy &&
  !((view.type === "panel" || view.panel) && view.cards?.length);

function addCard(config, index, section, card) {
  const next = structuredClone(config);
  const view = next.views[index];
  if (!view || !isEditable(view)) throw Error("Vue non modifiable.");
  const incoming = structuredClone(card);
  const sections = view.type === "sections";
  if (sections) incoming.grid_options ??= { columns: "full" };
  const existing = [...(view.cards ?? []),
    ...(view.sections ?? []).flatMap(item => item.cards ?? [])];
  if (existing.some(item => JSON.stringify(item) === JSON.stringify(incoming))) {
    throw Error("La carte C411 est déjà présente dans cette vue.");
  }
  if (!sections) {
    (view.cards ??= []).push(incoming);
  } else if (section === "new") {
    (view.sections ??= []).push({ type: "grid", cards: [incoming] });
  } else {
    const target = view.sections?.[Number(section)];
    if (!target || target.strategy || (target.type && target.type !== "grid")) {
      throw Error("Section non modifiable.");
    }
    (target.cards ??= []).push(incoming);
  }
  return next;
}

async function openWizard(hass, deviceId, opener) {
  const dialog = document.createElement("dialog");
  dialog.setAttribute("aria-labelledby", "c411-dashboard-title");
  dialog.style.cssText = "color:var(--primary-text-color);background:var(--card-background-color);border:1px solid var(--divider-color);border-radius:16px;padding:24px;width:min(420px,calc(100% - 48px));box-sizing:border-box";
  dialog.innerHTML = `<h2 id="c411-dashboard-title">Ajouter à un dashboard</h2>
    <form style="display:grid;gap:12px">
      <label>Tableau de bord <select name="dashboard" required disabled></select></label>
      <label>Vue <select name="view" required disabled></select></label>
      <label hidden>Section <select name="section"></select></label>
      <p role="status" style="margin:0"></p>
      <div style="display:flex;justify-content:flex-end;gap:8px">
        <button type="button" name="cancel">Annuler</button>
        <button type="submit" name="install" disabled>Ajouter la carte</button>
      </div>
    </form>`;
  document.body.append(dialog);
  dialog.addEventListener("close", () => { dialog.remove(); opener.focus(); }, { once: true });
  dialog.showModal();

  const form = dialog.querySelector("form");
  const { dashboard, view, section, cancel, install } = form.elements;
  const status = dialog.querySelector("[role=status]");
  const sectionLabel = section.parentElement;
  const requestConfig = path => hass.callWS({
    type: "lovelace/config", url_path: path === "lovelace" ? null : path, force: false,
  });
  let generation = 0;
  let config;
  let card;
  let saving = false;
  const option = (label, value, disabled = false) => {
    const item = new Option(label, value);
    item.disabled = disabled;
    return item;
  };

  function selectSection() {
    const selected = config?.views[Number(view.value)];
    sectionLabel.hidden = selected?.type !== "sections";
    if (!sectionLabel.hidden) {
      section.replaceChildren(option("Nouvelle section", "new"),
        ...(selected.sections ?? []).map((item, i) =>
          option(item.title || `Section ${i + 1}`, i,
            Boolean(item.strategy || (item.type && item.type !== "grid")))));
    }
    install.disabled = !selected || !isEditable(selected);
  }

  async function selectDashboard() {
    const request = ++generation;
    config = null;
    view.replaceChildren();
    view.disabled = install.disabled = sectionLabel.hidden = true;
    status.textContent = "Chargement des vues…";
    try {
      const next = await requestConfig(dashboard.value);
      if (request !== generation || !dialog.open) return;
      if (!next || "strategy" in next || !Array.isArray(next.views)) {
        throw Error("Ce dashboard est généré automatiquement. Choisis un dashboard modifiable.");
      }
      const first = next.views.findIndex(isEditable);
      if (first < 0) throw Error("Ce dashboard ne contient aucune vue modifiable.");
      config = next;
      view.replaceChildren(...next.views.map((item, i) =>
        option(item.title || `Vue ${i + 1}`, i, !isEditable(item))));
      view.value = String(first);
      view.disabled = false;
      status.textContent = "";
      selectSection();
    } catch (error) {
      if (request === generation && dialog.open) status.textContent = error.message;
    }
  }

  cancel.onclick = () => dialog.close();
  dialog.addEventListener("cancel", event => { if (saving) event.preventDefault(); });
  dashboard.onchange = selectDashboard;
  view.onchange = selectSection;
  form.onsubmit = async event => {
    event.preventDefault();
    if (saving || !config || install.disabled) return;
    saving = true;
    const path = dashboard.value;
    const index = Number(view.value);
    const destination = section.value;
    const controls = [dashboard, view, section, install, cancel];
    controls.forEach(control => { control.disabled = true; });
    status.textContent = "Ajout de la carte…";
    try {
      const current = await requestConfig(path);
      if (JSON.stringify(current) !== JSON.stringify(config)) {
        await selectDashboard();
        throw Error("Le tableau de bord a changé. Vérifie de nouveau la destination.");
      }
      const updated = addCard(current, index, destination, card);
      await hass.callWS({
        type: "lovelace/config/save", url_path: path === "lovelace" ? null : path,
        config: updated,
      });
      const link = document.createElement("a");
      link.href = `/${path}/${updated.views[index].path || index}`;
      link.textContent = "Ouvrir le tableau de bord";
      status.replaceChildren("Carte C411 ajoutée. ", link);
      cancel.textContent = "Fermer";
      cancel.disabled = false;
    } catch (error) {
      status.textContent = error.message || "Vérifie le tableau de bord avant de réessayer.";
      dashboard.disabled = section.disabled = cancel.disabled = false;
      view.disabled = !config;
      selectSection();
    } finally {
      saving = false;
    }
  };

  try {
    status.textContent = "Chargement des tableaux de bord…";
    const [generated, dashboards] = await Promise.all([
      hass.callWS({ type: "c411/dashboard_card", device_id: deviceId }),
      hass.callWS({ type: "lovelace/dashboards/list" }),
    ]);
    if (!dialog.open) return;
    card = generated;
    const overview = hass.panels?.lovelace;
    const choices = [
      { url_path: "lovelace", title: overview?.title || "Aperçu",
        mode: overview?.config?.mode || "storage" },
      ...dashboards.filter(item => item.url_path !== "lovelace"),
    ].filter(item => item.mode === "storage");
    if (!choices.length) throw Error("Aucun tableau de bord modifiable.");
    dashboard.replaceChildren(...choices.map(item => option(item.title, item.url_path)));
    dashboard.disabled = false;
    await selectDashboard();
  } catch (error) {
    status.textContent = error.message || "Impossible de préparer la carte C411.";
  }
}

function findDevicePage(root) {
  const page = root.querySelector("ha-config-device-page");
  if (page) return page;
  for (const element of root.querySelectorAll("*")) {
    if (element.shadowRoot) {
      const found = findDevicePage(element.shadowRoot);
      if (found) return found;
    }
  }
}

let checkedDevice;
let currentPage;
async function mount() {
  const deviceId = location.pathname.match(devicePath)?.[1];
  if (!deviceId) {
    checkedDevice = currentPage = undefined;
    return;
  }
  const app = document.querySelector("home-assistant");
  const hass = app?.hass;
  const page = app?.shadowRoot && findDevicePage(app.shadowRoot);
  const root = page?.shadowRoot;
  if (!hass?.user?.is_admin || !root) return;
  if (page !== currentPage || checkedDevice?.id !== deviceId) {
    currentPage = page;
    root.querySelector("#c411-add-dashboard")?.remove();
    const check = { id: deviceId };
    checkedDevice = check;
    try {
      await hass.callWS({ type: "c411/dashboard_card", device_id: deviceId, check_only: true });
      check.allowed = true;
    } catch {
      check.allowed = false;
    }
  }
  if (checkedDevice?.id !== deviceId || !checkedDevice.allowed ||
      currentPage !== page || location.pathname.match(devicePath)?.[1] !== deviceId ||
      root.querySelector("#c411-add-dashboard")) return;
  const sensors = [...root.querySelectorAll("ha-device-entities-card")].find(card =>
    card.entities?.some(entity => entity.entity_id.startsWith("sensor.")));
  const container = sensors?.parentElement;
  if (!container) return;
  const button = document.createElement("ha-button");
  button.id = "c411-add-dashboard";
  button.style.margin = "12px 16px";
  button.textContent = "Ajouter à un dashboard";
  button.onclick = () => openWizard(hass, deviceId, button);
  sensors.after(button);
}

setInterval(mount, 750);
