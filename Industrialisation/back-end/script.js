// =============================
// Config
// =============================
//const API_BASE = "http://127.0.0.1:8000";
const apiUrl = "https://radar-metier-or97.onrender.com";


let selectedSkillsCodes = [];

// =============================
// Utils
// =============================
function populateSelect(selectEl, items, defaultText, getValue, getLabel) {
    selectEl.innerHTML = "";
    const defaultOption = document.createElement("option");
    defaultOption.value = "";
    defaultOption.textContent = defaultText;
    selectEl.appendChild(defaultOption);

    if (!items || items.length === 0) return;

    items.forEach(item => {
        const option = document.createElement("option");
        option.value = getValue(item);
        option.textContent = getLabel(item);
        selectEl.appendChild(option);
    });
}

// =============================
// Chargement API
// =============================
async function loadDomaines() {
    try {
        const res = await fetch(`${apiUrl}/get_domaine_competence`, { method: "POST" ,
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({})});
        const data = await res.json();
        if (data.status === "success") {
            populateSelect(
                document.getElementById("select_domaineCompetence"),
                data.liste_domaine,
                "Sélectionnez votre domaine",
                d => d,
                d => d
            );
        }
    } catch (err) { console.error("Erreur domaines:", err); }
}

async function loadMacro(domain) {
    if (!domain) {
        populateSelect(document.getElementById("select_macroCompetence"), [], "Sélectionnez votre macro-compétence", d => d, d => d);
        return;
    }
    try {
        const res = await fetch(`${apiUrl}/get_macro_competence`, {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({ domaine_competence: domain })
        });
        const data = await res.json();
        if (data.status === "success") {
            populateSelect(
                document.getElementById("select_macroCompetence"),
                data.liste_macro_competence,
                "Sélectionnez votre macro-compétence",
                d => d,
                d => d
            );
        }
    } catch (err) { console.error("Erreur macro:", err); }
}

async function loadCompetences(macro) {
    if (!macro) {
        populateSelect(document.getElementById("select_Competence"), [], "Sélectionnez votre compétence", d => d.code, d => d.libelle);
        return;
    }
    try {
        const res = await fetch(`${apiUrl}/get_competence`, {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({ macro_competence: macro })
        });
        const data = await res.json();
        if (data.status === "success") {
            populateSelect(
                document.getElementById("select_Competence"),
                data.liste_competence,
                "Sélectionnez votre compétence",
                d => d.code,
                d => d.libelle
            );
        }
    } catch (err) { console.error("Erreur compétences:", err); }
}

async function loadRomeList(endpoint, selectId) {
    try {
        const res = await fetch(`${apiUrl}/${endpoint}`, { method: "POST" });
        const data = await res.json();
        if (data.status === "success") {
            const list = endpoint.includes("actuel") ? data.liste_rome_actuel : data.liste_rome_cible;
            populateSelect(
                document.getElementById(selectId),
                list,
                endpoint.includes("actuel") ? "Sélectionnez votre code rome actuel" : "Sélectionnez votre code rome ciblé",
                d => d.code_rome,
                d => `${d.code_rome} - ${d.libelle_rome}`
            );
        }
    } catch (err) { console.error(`Erreur ${selectId}:`, err); }
}

// =============================
// Ajouter compétence (auto ou manuel)
// =============================
function addSkill(code, libelle, type = "manuel") {
    if (!code || selectedSkillsCodes.includes(code)) return;

    selectedSkillsCodes.push(code);

    const skillsGrid = document.getElementById("skillsGrid");
    const skillItem = document.createElement("div");
    skillItem.classList.add("skill-tag");
    skillItem.textContent = `${libelle} (${type})`;
    skillItem.dataset.code = code;
    //skillItem.style.backgroundColor = type === "auto" ? "#eb8af8ff" : "#c480fcff";

    skillItem.addEventListener("click", () => {
        selectedSkillsCodes = selectedSkillsCodes.filter(c => c !== code);
        skillItem.remove();
        document.getElementById("predictBtn").disabled = selectedSkillsCodes.length === 0;
        updateProgressBar();
    });

    skillsGrid.appendChild(skillItem);

    document.getElementById("predictBtn").disabled = selectedSkillsCodes.length === 0;
    updateProgressBar();
}

function updateProgressBar() {
    const progressFill = document.getElementById("progressFill");
    const maxSkills = 20;
    const progress = Math.min(selectedSkillsCodes.length / maxSkills, 1);
    progressFill.style.width = `${progress * 100}%`;
}
// =============================
// Ajouter compétence manuelle
// =============================
function addSelectedCompetence() {
    const select = document.getElementById("select_Competence");
    const code = select.value;
    const libelle = select.options[select.selectedIndex]?.text;
    addSkill(code, libelle, "manuel");
}
// =============================
// Charger compétences par ROME actuel
// =============================
async function loadCompetencesByRome(codeRome) {
    if (!codeRome) return;
    try {
        const res = await fetch(`${apiUrl}/get_competences_by_rome?code_rome=${codeRome}`, { method: "POST" });
        const data = await res.json();
        if (data.status === "success") {
            data.competences.forEach(c => addSkill(c.code_ogr_competence, c.libelle_competence, "auto"));
        }
    } catch (err) { console.error("Erreur compétences ROME:", err); }
}


// =============================
// Récupérer compétences du métier ciblé
// =============================
async function loadCompetencesCible(codeRomeCible) {
    if (!codeRomeCible) return [];
    try {
        const res = await fetch(`${apiUrl}/get_competences_by_rome?code_rome=${codeRomeCible}`, { method: "POST" });
        const data = await res.json();
        if (data.status === "success") {
            return data.competences.map(c => ({ code: String(c.code_ogr_competence), libelle: c.libelle_competence }));
        }
        return [];
    } catch (err) {
        console.error("Erreur chargement compétences ciblées :", err);
        return [];
    }
}

// =============================
// Prédiction + comparaison compétences
// =============================
async function predictJobs() {
    if (selectedSkillsCodes.length === 0) {
        alert("Veuillez ajouter au moins une compétence !");
        return;
    }

    const payload = { skills: selectedSkillsCodes.map(String) };
    console.log("Payload envoyé :", payload);

    try {
        const res = await fetch(`${apiUrl}/predict`, {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify(payload)
        });

        if (!res.ok) throw new Error(`Erreur HTTP ${res.status}`);
        const data = await res.json();
        console.log("Résultat prédiction :", data);

        const resultPanelContent = document.getElementById('resultPanelContent');
        const resultPanelStatus = document.getElementById('resultStatus');
        resultPanelContent.innerHTML = "";

        // --- Affichage prédictions ---
if (data.result && data.result.predictions && data.result.predictions.length > 0) {
    // Créer un bloc global pour les prédictions
    const predictJobBlock = document.createElement("div");
    predictJobBlock.className = "skills-block acquired-skills";

    // Ajouter le titre
    const predictJobTitle = document.createElement("div");
    predictJobTitle.textContent = "Les métiers prédits par notre IA :";
    predictJobTitle.style.fontWeight = "bold";
    predictJobTitle.style.marginBottom = "5px";
    predictJobBlock.appendChild(predictJobTitle);

    // Ajouter chaque prédiction
    data.result.predictions.forEach(item => {
        const predictJobDiv = document.createElement("div");
        predictJobDiv.textContent = item?.libelle || "Aucun résultat";
        predictJobBlock.appendChild(predictJobDiv);

        const predictMeterDiv = document.createElement("div");
        predictMeterDiv.className = "confidence-meter";

        const predictLabelSpan = document.createElement("span");
        predictLabelSpan.textContent = "Indice de fiabilité : ";
        predictMeterDiv.appendChild(predictLabelSpan);

        const predictBarDiv = document.createElement("div");
        predictBarDiv.className = "confidence-bar";

        const predictFillDiv = document.createElement("div");
        predictFillDiv.className = "confidence-fill";
        const confidence = Math.round(item?.score * 100) || 0;
        predictFillDiv.style.width = confidence + "%";
        predictBarDiv.appendChild(predictFillDiv);

        predictMeterDiv.appendChild(predictBarDiv);

        const predictPercentSpan = document.createElement("span");
        predictPercentSpan.textContent = confidence + "%";
        predictMeterDiv.appendChild(predictPercentSpan);

        predictJobBlock.appendChild(predictMeterDiv);
    });

    // Ajouter tout le bloc au panneau
    resultPanelContent.appendChild(predictJobBlock);
} else {
    resultPanelContent.innerHTML = "<p>Aucune prédiction disponible pour ces compétences.</p>";
}


// --- Comparaison compétences ---
const codeRomeCible = document.getElementById("select_code_rome_ciblé").value;

if (codeRomeCible) {
    const cibleSkills = await loadCompetencesCible(codeRomeCible);
    const currentSkills = selectedSkillsCodes.map(String);

    // Compétences manquantes et acquises
    const missingSkills = cibleSkills.filter(s => !currentSkills.includes(s.code));
    const acquiredSkills = cibleSkills.filter(s => currentSkills.includes(s.code));

    // --- Création du bloc compétences acquises ---
    if (acquiredSkills.length > 0) {
        const acquiredBlock = document.createElement("div");
        acquiredBlock.className = "skills-block acquired-skills";
        
        const acquiredTitle = document.createElement("div");
        acquiredTitle.textContent = "Compétences déjà acquises pour le métier ciblé :";
        acquiredTitle.style.fontWeight = "bold";
        acquiredTitle.style.marginBottom = "5px";
        acquiredBlock.appendChild(acquiredTitle);

        const ulAcquired = document.createElement("ul");
        acquiredSkills.forEach(s => {
            const li = document.createElement("li");
            li.textContent = s.libelle;
            li.style.color = "#28a745"; // vert pour acquis
            ulAcquired.appendChild(li);
        });
        acquiredBlock.appendChild(ulAcquired);

        resultPanelContent.appendChild(acquiredBlock);
    }

    // --- Création du bloc compétences manquantes ---
    if (missingSkills.length > 0) {
        const missingBlock = document.createElement("div");
        missingBlock.className = "skills-block missing-skills";
        
        const missingTitle = document.createElement("div");
        missingTitle.textContent = "Compétences manquantes pour le métier ciblé :";
        missingTitle.style.fontWeight = "bold";
        missingTitle.style.marginBottom = "5px";
        missingBlock.appendChild(missingTitle);

        const ulMissing = document.createElement("ul");
        missingSkills.forEach(s => {
            const li = document.createElement("li");
            li.textContent = s.libelle;
            li.style.color = "#dc3545"; // rouge pour manquant
            ulMissing.appendChild(li);
        });
        missingBlock.appendChild(ulMissing);

        resultPanelContent.appendChild(missingBlock);
    }

    // --- Message si tout est acquis ---
    if (missingSkills.length === 0 && acquiredSkills.length > 0) {
        const msg = document.createElement("div");
        msg.textContent = "Vous possédez déjà toutes les compétences du métier ciblé.";
        msg.style.marginTop = "10px";
        resultPanelContent.appendChild(msg);
    }
}
        resultPanelStatus.textContent = "Basé sur l'analyse de vos compétences sélectionnées";

    } catch (err) {
        console.error("Erreur prédiction :", err);
        const resultPanelContent = document.getElementById('resultPanelContent');
        const resultPanelStatus = document.getElementById('resultStatus');
        resultPanelContent.innerHTML = `<p style="color:red">Erreur lors de la prédiction : ${err.message}</p>`;
        resultPanelStatus.textContent = "Erreur lors de l'analyse";
    }

    document.getElementById('resultPanel').classList.add('show');
}

// =============================
// Filtrage ROME séparé
// =============================
function filterRomeByLetter(selectId, letter) {
    const selectEl = document.getElementById(selectId);
    for (let i = 0; i < selectEl.options.length; i++) {
        const option = selectEl.options[i];
        if (!letter || option.value.startsWith(letter.toUpperCase())) {
            option.style.display = "";
        } else {
            option.style.display = "none";
        }
    }
}

// =============================
// DOMContentLoaded
// =============================
document.addEventListener("DOMContentLoaded", () => {
    loadDomaines();
    loadRomeList("get_rome_actuel_list", "select_code_rome_actuel");
    loadRomeList("get_rome_cible_list", "select_code_rome_ciblé");

    document.getElementById("select_domaineCompetence").addEventListener("change", e => loadMacro(e.target.value));
    document.getElementById("select_macroCompetence").addEventListener("change", e => loadCompetences(e.target.value));
    document.getElementById("addSkillBtn").addEventListener("click", addSelectedCompetence);

    document.getElementById("select_code_rome_actuel").addEventListener("change", e => {
        const codeRome = e.target.value;
        if (codeRome) {
            selectedSkillsCodes = [];
            document.getElementById("skillsGrid").innerHTML = "";
            loadCompetencesByRome(codeRome);
            updateProgressBar();
        }
    });

    document.getElementById("predictBtn").addEventListener("click", predictJobs);

    // Filtres séparés
    document.getElementById("romeLetterFilterActuel").addEventListener("change", e => {
        filterRomeByLetter("select_code_rome_actuel", e.target.value);
    });
    document.getElementById("romeLetterFilterCible").addEventListener("change", e => {
        filterRomeByLetter("select_code_rome_ciblé", e.target.value);
    });
});

/////////////////////////////////////////////////////////////////////////////////////////////////

loadRomeList("get_rome_actuel_list", "select_code_rome_actuel").then(() => {
    const searchInput = document.getElementById("searchRomeInput");
    const autocompleteList = document.getElementById("autocompleteList");
    const select = document.getElementById("select_code_rome_actuel");

    const allOptions = Array.from(select.options).map(opt => ({
        code: opt.value,
        libelle: opt.text
    }));

    function showFilteredOptions(query) {
        autocompleteList.innerHTML = "";
        if (!query) {
            autocompleteList.style.display = "none";
            return;
        }

        const filtered = allOptions.filter(opt =>
            opt.libelle.toLowerCase().includes(query.toLowerCase()) ||
            opt.code.toLowerCase().includes(query.toLowerCase())
        );

        if (filtered.length === 0) {
            autocompleteList.style.display = "none";
            return;
        }

        filtered.forEach(opt => {
            const div = document.createElement("div");
            div.className = "autocomplete-item";
            div.textContent = `${opt.libelle} (${opt.code})`;

            div.addEventListener("click", () => {
                // Mettre le libellé dans la barre de recherche
                searchInput.value = opt.libelle;

                // Sélectionner la bonne option dans le select
                select.value = opt.code;

                // 👉 Déclencher le "change" du select comme si l’utilisateur avait cliqué dessus
                select.dispatchEvent(new Event("change"));

                // Cacher la liste
                autocompleteList.style.display = "none";
            });

            autocompleteList.appendChild(div);
        });

        autocompleteList.style.display = "block";
    }

    searchInput.addEventListener("input", () => {
        showFilteredOptions(searchInput.value.trim());
    });

    document.addEventListener("click", (e) => {
        if (!e.target.closest(".autocomplete-container")) {
            autocompleteList.style.display = "none";
        }
    });
});
loadRomeList("get_rome_cible_list", "select_code_rome_ciblé").then(() => {
    const searchInputCible = document.getElementById("searchRomeInputCible");
    const autocompleteListCible = document.getElementById("autocompleteListCible");
    const selectCible = document.getElementById("select_code_rome_ciblé");

    const allOptionsCible = Array.from(selectCible.options).map(opt => ({
        code: opt.value,
        libelle: opt.text
    }));

    function showFilteredOptionsCible(query) {
        autocompleteListCible.innerHTML = "";
        if (!query) {
            autocompleteListCible.style.display = "none";
            return;
        }

        const filtered = allOptionsCible.filter(opt =>
            opt.libelle.toLowerCase().includes(query.toLowerCase()) ||
            opt.code.toLowerCase().includes(query.toLowerCase())
        );

        if (filtered.length === 0) {
            autocompleteListCible.style.display = "none";
            return;
        }

        filtered.forEach(opt => {
            const div = document.createElement("div");
            div.className = "autocomplete-item";
            div.textContent = `${opt.libelle} (${opt.code})`;

            div.addEventListener("click", () => {
                // Mettre le libellé choisi dans la barre de recherche
                searchInputCible.value = opt.libelle;

                // Sélectionner l'option dans le select
                selectCible.value = opt.code;

                // 👉 Déclencher le change pour lancer ton code de comparaison compétences
                selectCible.dispatchEvent(new Event("change"));

                // Cacher la liste
                autocompleteListCible.style.display = "none";
            });

            autocompleteListCible.appendChild(div);
        });

        autocompleteListCible.style.display = "block";
    }

    searchInputCible.addEventListener("input", () => {
        showFilteredOptionsCible(searchInputCible.value.trim());
    });

    document.addEventListener("click", (e) => {
        if (!e.target.closest(".autocomplete-container")) {
            autocompleteListCible.style.display = "none";
        }
    });
});
//////////////////////////////////////////////////////////////////////////////////

const { createClient } = supabase;

// On initialise client Supabase
const SUPABASE_URL = "https://bhckzdwrhhfaxbidmwpm.supabase.co";
const SUPABASE_ANON_KEY = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6ImJoY2t6ZHdyaGhmYXhiaWRtd3BtIiwicm9sZSI6ImFub24iLCJpYXQiOjE3NTE2MTE1NzAsImV4cCI6MjA2NzE4NzU3MH0.qXODxUXjpfC9qTIHXBWcHXTLioJGXsnSrQqsJA1ugf4";       // remplace par ta clé anonyme
const client = createClient(SUPABASE_URL, SUPABASE_ANON_KEY);

let rncpData = [];

// --- Chargement CSV ---
async function loadRncpCsv(path = "RNCP_all.csv", bucket = "rncp") {
      try {
        console.log(`Téléchargement du fichier ${path} depuis le bucket "${bucket}"...`);
        const { data, error } = await client.storage.from(bucket).download(path);

        if (error) throw error;

        // Lire le texte du fichier
        const text = await data.text();

// Parser le CSV avec PapaParse
        return new Promise((resolve, reject) => {
            Papa.parse(text, {
                header: true,
                skipEmptyLines: true,
                complete: function(results) {
                    rncpData = results.data.map(row => {
                        // Récupérer les 5 codes ROME
                        const romes = [];
                        for (let i = 1; i <= 5; i++) {
                            const codeKey = `codes_rome_code${i}`;
                            if (row[codeKey] && row[codeKey].trim() !== "") {
                                romes.push(row[codeKey].trim());
                            }
                        }

                        // Parsing date (dd/mm/yyyy)
                        let dateFin = null;
                        if (row.date_fin_enregistrement && row.date_fin_enregistrement.trim() !== "") {
                            const parts = row.date_fin_enregistrement.trim().split("/");
                            if (parts.length === 3) {
                                const day = parseInt(parts[0], 10);
                                const month = parseInt(parts[1], 10) - 1;
                                const year = parseInt(parts[2], 10);
                                const parsed = new Date(year, month, day);
                                if (!isNaN(parsed)) dateFin = parsed;
                            }
                        }

                        return {
                            code_rncp: row.numero_fiche,
                            libelle: row.intitule || row.abrege_libelle || "",
                            romes,
                            dateFin,
                            niveau: row.nomenclature_europe_intitule || ""
                        };
                    });

                    console.log(`${rncpData.length} fiches RNCP chargées.`);
                    resolve(rncpData);
                },
                error: reject
            });
        });

    } catch (err) {
        console.error("Erreur lors du chargement du CSV depuis Supabase :", err);
        throw err;
    }
}

// --- Filtrer + trier formations ---
function getFormationsForRome(romeCode) {
    if (!romeCode) return [];
    const today = new Date();

    let results = rncpData.filter(f =>
        f.romes.includes(romeCode) &&
        f.dateFin && f.dateFin >= today
    );

    // Tri alphabétique
    results.sort((a, b) => a.libelle.localeCompare(b.libelle));

    return results;
}

// --- Affichage ---
function renderRncpResults(formations) {
    const container = document.getElementById("rncpResults");
    container.innerHTML = "";
    if (formations.length === 0) {
        container.innerHTML = "<p>Aucune formation RNCP valide trouvée.</p>";
        return;
    }

    const ul = document.createElement("ul");
    ul.style.padding = "0";
    ul.style.listStyle = "none";

    formations.forEach(f => {
        const li = document.createElement("li");

        // Extraire uniquement les chiffres du code RNCP
        const numericCode = f.code_rncp.replace(/\D/g, '');
        const rncpUrl = `https://www.francecompetences.fr/recherche/rncp/${numericCode}`;

        // Stocker le code RNCP dans un data-attribute pour le PDF
        li.dataset.code_rncp = f.code_rncp;

        li.innerHTML = `
            <strong>${f.libelle}</strong> (${f.code_rncp})<br>
            Niveau : ${f.niveau || "Non précisé"}<br>
            Valide jusqu'au : ${f.dateFin ? f.dateFin.toLocaleDateString() : "Inconnue"}<br>
            <a href="${rncpUrl}" target="_blank">Voir la fiche RNCP</a>
        `;
        li.style.marginBottom = "1rem";
        ul.appendChild(li);
    });

    container.appendChild(ul);
}

// --- Initialisation ---
document.addEventListener("DOMContentLoaded", () => {
    const selectCible = document.getElementById("select_code_rome_ciblé");

    // Charger le fichier CSV depuis Supabase
    loadRncpCsv("RNCP_all.csv", "rncp")
        .then(() => console.log("RNCP chargé depuis Supabase :", rncpData.length))
        .catch(err => console.error("Erreur chargement RNCP:", err));

    selectCible.addEventListener("change", (e) => {
        const rome = e.target.value.substring(0, 5); // garder juste le code ROME
        const formations = getFormationsForRome(rome);
        renderRncpResults(formations);
    });
});
// =============================
// Barre de recherche COMPÉTENCES
// =============================
let allCompetences = [];

document.addEventListener("DOMContentLoaded", async () => {
  try {
    const res = await fetch(`${apiUrl}/get_all_competences`, { method: 'get' });
    const data = await res.json();
    if (data.status === 'success') {
      allCompetences = data.liste_competence;
      console.log('Toutes les compétences chargées', allCompetences.length);
    }
  } catch (err) {
    console.error(err);
  }
});
const searchInput = document.getElementById('searchSkillInput');
const autocompleteList = document.getElementById('autocompleteSkillList');

searchInput.addEventListener('input', () => {
    const query = searchInput.value.toLowerCase();
    autocompleteList.innerHTML = '';

    if (!query) return;

    const filtered = allCompetences
        .filter(c => c.libelle.toLowerCase().includes(query))
        .slice(0, 100); // limiter à 100 résultats

    filtered.forEach(c => {
        const item = document.createElement('div');
        item.classList.add('autocomplete-item');
        item.textContent = c.libelle;
        item.addEventListener('click', () => {
            searchInput.value = c.libelle;
            autocompleteList.innerHTML = '';
        });
        autocompleteList.appendChild(item);
    });
});
const addSkillBtn = document.getElementById('addSkillBtn');
const skillsGrid = document.getElementById('skillsGrid');

addSkillBtn.addEventListener('click', () => {
    const selectedSkill = searchInput.value.trim();
    if (!selectedSkill) return;

    // Trouver l'objet compétence correspondant
    const skillObj = allCompetences.find(c => c.libelle === selectedSkill);
    if (!skillObj) return alert("Compétence invalide.");

    // Vérifier si elle est déjà dans la grille
    if ([...skillsGrid.children].some(div => div.dataset.code === skillObj.code.toString())) {
        return; // ignore si déjà ajouté
    }
    // Ajouter au tableau selectedSkillsCodes pour la prédiction
    addSkill(skillObj.code, skillObj.libelle, "manuel"); // ← remplace tout le reste de la création manuelle
     
    // Reset input et liste auto
    searchInput.value = '';
    autocompleteList.innerHTML = '';
});
    
//////////////////////////////////////////////////////////////////////////////////
////////////////////PDF
/////////////////////////////////////////////////////////////////////////////////
document.addEventListener("DOMContentLoaded", () => {
  const sendBtn = document.getElementById("sendBtn");
  if (!sendBtn) return console.error("Bouton #sendBtn introuvable !");

  sendBtn.addEventListener("click", async () => {
    try {
      if (!window.jspdf) return alert("Erreur : jsPDF n'est pas chargé !");
      const { jsPDF } = window.jspdf;
      const doc = new jsPDF({ unit: "pt", format: "a4" });

      const pageW = doc.internal.pageSize.getWidth();
      const pageH = doc.internal.pageSize.getHeight();
      const margin = 40;
      const padding = 10;
      const footerHeight = 30;
      let cursorY = margin;

      // ---------- UTILITAIRES ----------
      function drawBackground() {
        doc.setFillColor(248, 250, 252);
        doc.rect(0, 0, pageW, pageH, "F");
      }

      function smartSplit(text, maxW) {
        return doc.splitTextToSize(text, maxW);
      }

      function addFooter() {
        const pageNum = doc.internal.getNumberOfPages();
        doc.setFontSize(9);
        doc.setFont("helvetica", "italic");
        doc.setTextColor(120);
        doc.text(`Page ${pageNum} - Document généré par Radar_Métier`, pageW / 2, pageH - 15, { align: "center" });
      }

      drawBackground();

      // ---------- TITRE PRINCIPAL ----------
      doc.setFont("helvetica", "bold");
      doc.setFontSize(22);
      doc.setTextColor(18, 155, 137);
      doc.text("RÉSULTAT DE L'ANALYSE", pageW / 2, cursorY, { align: "center" });
      cursorY += 30;

      doc.setDrawColor(43, 210, 240);
      doc.setLineWidth(3);
      const lineW = 80;
      doc.line((pageW - lineW) / 2, cursorY, (pageW + lineW) / 2, cursorY);
      cursorY += 30;

///////////////////////////////////////////////
      // ---------- BLOC 1 : CRITÈRES ----------
///////////////////////////////////////////////

function writeCriteriaBlock() {
  const boxX = margin;
  const boxW = pageW - 2 * margin;
  const pad = padding;
  const fontSize = 10;
  const lineH = Math.ceil(fontSize * 1.3);
  const maxTextWidth = boxW - 2 * pad;

  const jobActuel =
    (document.getElementById("searchRomeInput")?.value || "").trim() ||
    (document.getElementById("select_code_rome_actuel")?.selectedOptions?.[0]?.text || "").trim() ||
    "Non renseigné";

  const jobCible =
    (document.getElementById("searchRomeInputCible")?.value || "").trim() ||
    (document.getElementById("select_code_rome_ciblé")?.selectedOptions?.[0]?.text || "").trim() ||
    "Non renseigné";

  let skills = Array.from(document.querySelectorAll("#skillsGrid > div"))
    .map(el => el.textContent.trim())
    .filter(Boolean);
  if (!skills.length) skills = ["Aucune compétence sélectionnée"];

  const items = [
    { text: "Vos critères sélectionnés", bold: true, isTitle: true },
    { text: "" },
    { text: "Métier actuel :", bold: true }, { text: jobActuel },
    { text: "" },
    { text: "Compétences :", bold: true },
    ...skills.map(s => ({ text: "• " + s, indent: 12 })),
    { text: "" },
    { text: "Métier ciblé :", bold: true }, { text: jobCible },
  ];

  const lines = [];
  doc.setFontSize(fontSize);
  items.forEach(it => {
    const { text, bold, indent = 0, isTitle } = it;
    const parts = smartSplit(text, maxTextWidth - indent);
    parts.forEach(p => lines.push({ text: p, bold, indent, isTitle }));
  });

  let lineIndex = 0;
  while (lineIndex < lines.length) {
    const availableH = pageH - cursorY - footerHeight - pad;
    const linesFit = Math.floor(availableH / lineH) || 1;
    const slice = lines.slice(lineIndex, lineIndex + linesFit);
    const blockH = slice.length * lineH + pad * 2;

    doc.setFillColor(235, 250, 245);
    doc.setLineWidth(2);        // ← ici tu définis l’épaisseur
    doc.setDrawColor(0, 128, 128);
    doc.roundedRect(boxX, cursorY, boxW, blockH, 6, 6, "FD");


    let y = cursorY + pad + lineH / 2;
    slice.forEach(l => {
      if (l.isTitle) {
        doc.setFont("helvetica", "bold");
        doc.setFontSize(14);
        doc.setTextColor(18, 155, 137);
        doc.text(l.text, pageW / 2, y, { align: "center" });
      } else {
        doc.setFont("helvetica", l.bold ? "bold" : "normal");
        doc.setFontSize(fontSize);
        doc.setTextColor(0, 0, 0);
        doc.text(l.text, boxX + pad + (l.indent || 0), y);
      }
      y += lineH;
    });

    lineIndex += linesFit;
    cursorY += blockH;

    if (lineIndex < lines.length) {
      addFooter();
      doc.addPage();
      drawBackground();
      cursorY = margin;
    } else {
      cursorY += 15;
    }
  }
}


/////////////////////////////////////////////////
// ---------- BLOC 2 : MÉTIERS PRÉDITS ----------
/////////////////////////////////////////////////

function writePredictedBlockFromDOM() {
  const boxX = margin;
  const boxW = pageW - 2 * boxX;
  const pad = 12;
  const jobFontSize = 11;
  const smallFont = 10;
  const barH = 10;
  const spacingAfter = 12;
  const lineGap = 8;

  const container = document.getElementById("resultPanelContent");
  if (!container) return;

  const predictions = [];
  const meters = container.querySelectorAll(".confidence-meter");
  meters.forEach(meter => {
    const jobEl = meter.previousElementSibling;
    const jobName = jobEl?.textContent?.trim() || "Aucun résultat";
    let confidence = 0;
    const fill = meter.querySelector(".confidence-fill");
    if (fill && fill.style.width) confidence = parseFloat(fill.style.width.replace("%","")) || 0;
    predictions.push({ jobName, confidence });
  });
  if (!predictions.length) return;

  let i = 0;
  while (i < predictions.length) {
    const availableH = pageH - cursorY - footerHeight - 10;
    const maxItems = Math.floor((availableH - 2*pad - 20)/(jobFontSize + barH + spacingAfter + lineGap));
    const slice = predictions.slice(i, i + Math.max(1,maxItems));

    const blockHeight = slice.length * (jobFontSize + barH + spacingAfter + lineGap) + 2*pad + 20;
    doc.setFillColor(255,255,255);
    doc.setDrawColor(18,155,137);
    doc.setLineWidth(2);
    doc.roundedRect(boxX, cursorY, boxW, blockHeight, 10, 10, "FD");

    // Titre centré
    doc.setFont("helvetica", "bold");
    doc.setFontSize(14);
    doc.setTextColor(18, 155, 137);
    doc.text("Les métiers prédits par notre IA", pageW / 2, cursorY + pad + 14, { align: "center" });

    let y = cursorY + pad + 30;

    slice.forEach(pred => {
      const startColor = [18, 224, 194];  // turquoise clair
      const endColor = [0, 128, 128];     // turquoise foncé
      const textLabel = "Indice de fiabilité :";
      doc.setFont("helvetica","normal");
      doc.setFontSize(smallFont);
      const labelWidth = doc.getTextWidth(textLabel);
      const barW = boxW - 2*pad - labelWidth - 30;

      // Nom du métier
      doc.setFont("helvetica","bold");
      doc.setFontSize(jobFontSize);
      doc.setTextColor(0,0,0);
      const jobY = y + jobFontSize;
      doc.text(pred.jobName, boxX + pad, jobY);

      // Texte "Indice de fiabilité :"
      const textY = jobY + lineGap + smallFont / 2;
      doc.setFont("helvetica","normal");
      doc.setFontSize(smallFont);
      doc.text(textLabel, boxX + pad, textY);

      // Barre grise
      const barX = boxX + pad + labelWidth + 6;
      const barY = jobY + lineGap;
      doc.setFillColor(230,230,230);
      doc.roundedRect(barX, barY, barW, barH, barH/2, barH/2, "F");

      // Dégradé turquoise
      const fillW = Math.max(1, Math.round((barW * pred.confidence)/100));
      const steps = Math.min(120, Math.max(20, Math.floor(fillW/2)));
      const segW = fillW/steps;
      for (let j=0;j<steps;j++){
        const ratio = j/(steps-1||1);
        const r = Math.round(startColor[0] + (endColor[0]-startColor[0])*ratio);
        const g = Math.round(startColor[1] + (endColor[1]-startColor[1])*ratio);
        const b = Math.round(startColor[2] + (endColor[2]-startColor[2])*ratio);
        const xPos = barX + j*segW;
        const wPos = segW + 0.4;
        const rx = Math.min(barH/2, wPos/2);
        doc.setFillColor(r,g,b);
        const clippedW = Math.max(0,Math.min(wPos, barX+fillW-xPos));
        if(clippedW>0) doc.roundedRect(xPos, barY, clippedW, barH, rx, rx,"F");
      }

      // Pourcentage
      doc.setFont("helvetica","bold");
      doc.setFontSize(smallFont);
      doc.text(`${Math.round(pred.confidence)}%`, barX + barW + 4, textY);

      // Passage à la ligne suivante
      y += jobFontSize + barH + spacingAfter + lineGap;
    });

    cursorY += blockHeight + 10;
    i += slice.length;

    if(i < predictions.length){
      addFooter();
      doc.addPage();
      drawBackground();
      cursorY = margin;
    }
  }
}


/////////////////////////////////////////////////
// ---------- BLOC 3 COMPÉTENCES ----------
/////////////////////////////////////////////////

function writeSkillsBlock(selector, options) {
  const nodes = Array.from(document.querySelectorAll(selector));
  if (!nodes.length) return;

  const skills = nodes.map(n => n.textContent.trim()).filter(Boolean);
  if (!skills.length) return;

  const boxX = margin;
  const boxW = pageW - 2 * margin;
  const pad = 12;
  const fontSize = 10;
  const titleFontSize = options.titleFontSize || fontSize + 2;
  const lineH = Math.ceil(fontSize * 1.3);
  const indentPx = 12;
  const maxTextWidth = boxW - 2 * pad;

  // Préparer toutes les lignes
  const allLines = [];
  skills.forEach(skill => {
    const wrapped = doc.splitTextToSize(skill, maxTextWidth - indentPx);
    allLines.push({ text: "• " + (wrapped[0] || ""), indent: 0 });
    for (let k = 1; k < wrapped.length; k++) {
      allLines.push({ text: wrapped[k], indent: indentPx });
    }
  });

  let i = 0;
  while (i < allLines.length) {
    const availableHInitial = pageH - cursorY - footerHeight - pad;
    const titleAreaH = titleFontSize + 6;
    if (availableHInitial < titleAreaH + lineH + 2 * pad) {
      addFooter();
      doc.addPage();
      drawBackground();
      cursorY = margin;
    }

    const availableH = pageH - cursorY - footerHeight - pad;
    const maxLines = Math.max(1, Math.floor((availableH - titleAreaH - 2 * pad) / lineH));
    const slice = allLines.slice(i, i + maxLines);
    const blockH = titleAreaH + slice.length * lineH + 2 * pad;

    // Dessiner l'encadré
    doc.setDrawColor(...options.borderColor);
    doc.setLineWidth(2);
    doc.setFillColor(...options.bgColor);
    doc.roundedRect(boxX, cursorY, boxW, blockH, 10, 10, "FD");

    // Titre centré
    doc.setFont("helvetica", "bold");
    doc.setFontSize(titleFontSize);
    doc.setTextColor(...options.titleColor);
    doc.text(options.title, pageW / 2, cursorY + pad + titleFontSize, { align: "center" });

    // Contenu sous le titre avec saut de ligne
    let yCursor = cursorY + pad + titleAreaH + lineH; // saut d’une ligne après le titre
    doc.setFont("helvetica", "normal");
    doc.setFontSize(fontSize);
    doc.setTextColor(0, 0, 0);

    slice.forEach(line => {
      doc.text(line.text, boxX + pad + line.indent, yCursor);
      yCursor += lineH;
    });

    i += slice.length;
    cursorY += blockH + 10;

    if (i < allLines.length) {
      addFooter();
      doc.addPage();
      drawBackground();
      cursorY = margin;
    }
  }
}

/////////////////////////////////////////////////
//bloc 4  RNCP AVEC ENCADRÉ GLOBAL ----------
/////////////////////////////////////////////////

function writeRncpBlocks() {
  const rncpNodes = Array.from(document.querySelectorAll("#rncpResults li"));
  if (!rncpNodes.length) return;

  const boxX = margin;
  const boxW = pageW - 2 * margin;
  const pad = 6;
  const miniPad = 6;
  const fontSize = 10;
  const titleFontSize = 14;
  const lineH = Math.ceil(fontSize * 1.3);
  const pageHeight = pageH - footerHeight - margin;

  let pageStarted = false;
  let blocStartY = 0;
  let blocContentHeight = 0;

  function drawRncpFrame() {
    if (blocContentHeight > 0) {
      doc.setDrawColor(18, 155, 137);
      doc.setLineWidth(2);
      doc.roundedRect(boxX, blocStartY, boxW, blocContentHeight + pad, 10, 10, "S");
    }
  }

  rncpNodes.forEach((li, idx) => {
    const text = li.textContent.replace(/\s+/g, " ").trim();
    const libelle = li.querySelector("strong")?.textContent?.trim() || "Non renseigné";

    const niveauMatch = text.match(/Niveau(?:\s*(?:de|du|d’|d')?\s*(?:qualification|RNCP|certification|cadre national des certifications)?)?\s*[:\-]?\s*(?:Niveau\s*)?([0-9IVX]+)/i);
    const niveau = niveauMatch ? niveauMatch[1] : "Non précisé";

    const dateMatch = text.match(/Valide\s*(?:jusqu.?au|jusqu.?à)\s*[:\-]?\s*([0-9/]+)/i);
    const dateFin = dateMatch ? dateMatch[1] : "Non renseignée";

    const codeRncp = li.dataset?.code_rncp || "0000";
    const url = `https://www.francecompetences.fr/recherche/rncp/${codeRncp.replace(/\D/g, "")}`;

    const libelleLines = doc.splitTextToSize(`${libelle}`, boxW - 4 * miniPad);
    const lines = [
      ...libelleLines,
      `Code RNCP : ${codeRncp.replace(/^RNCP\s*/i, "")}`,
      `Niveau : ${niveau}`,
      `Valide jusqu'au : ${dateFin}`,
      "Voir la fiche RNCP →"
    ];

    const textHeight = lines.length * lineH;
    const miniBlockHeight = textHeight + 4 * miniPad;

    // --- SAUT DE PAGE SI BESOIN ---
    if (cursorY + miniBlockHeight + pad > pageHeight) {
      drawRncpFrame();
      addFooter();
      doc.addPage();
      drawBackground();
      cursorY = margin;
      pageStarted = false;
      blocContentHeight = 0;
    }

    // --- TITRE DANS L'ENCADRÉ ---
    if (!pageStarted) {
      blocStartY = cursorY;
      const titleHeight = titleFontSize + pad;

      // Dessiner l'encadré global plus tard (blocContentHeight)
      // On réserve l'espace pour le titre
      cursorY += titleHeight;

      // Dessiner le titre à l'intérieur du bloc
      doc.setFont("helvetica", "bold");
      doc.setFontSize(titleFontSize);
      doc.setTextColor(18, 155, 137);
      doc.text("Les formations RNCP en rapport avec le métier ciblé", pageW / 2, blocStartY + pad + titleFontSize / 2, { align: "center" });

      pageStarted = true;
    }

    // --- MINI-BLOC ---
    doc.setDrawColor(18, 155, 137);
    doc.setLineWidth(0.5);
    doc.roundedRect(boxX + 6, cursorY, boxW - 12, miniBlockHeight, 6, 6, "S");

    const startY = cursorY + (miniBlockHeight - textHeight) / 2 + lineH / 2;
    let y = startY;

    lines.forEach((line, i) => {
      if (line.startsWith("Voir la fiche")) {
        doc.setFont("helvetica", "bold");
        doc.setTextColor(18, 155, 137);
        doc.textWithLink("Voir la fiche RNCP", boxX + 2 * miniPad + 6, y, { url });
      } else {
        doc.setFont("helvetica", "normal");
        doc.setFontSize(10);
        doc.setTextColor(0, 0, 0);
        doc.text(line, boxX + 2 * miniPad + 6, y);
      }
      y += lineH;
    });

    cursorY += miniBlockHeight + miniPad;
    blocContentHeight = cursorY - blocStartY;
  });

  drawRncpFrame();
}
/////////////////////////////////////////////////
      // ---------- EXÉCUTION ----------
/////////////////////////////////////////////////

      writeCriteriaBlock();

      // Afficher les métiers prédits
      writePredictedBlockFromDOM();

      // Utilisation pour les deux blocs
      writeSkillsBlock(".acquired-skills li", {
        title: "Compétences déjà acquises pour le métier ciblé",
        titleFontSize: 14,
        titleColor: [18, 155, 137],
        borderColor: [18, 155, 137],
        bgColor: [235, 250, 245]
      });

      writeSkillsBlock(".missing-skills li", {
        title: "Compétences manquantes pour le métier ciblé",
        titleFontSize: 14,
        titleColor: [220, 38, 38],
        borderColor: [220, 38, 38],
        bgColor: [255, 235, 235]
      });
      writeRncpBlocks();

      addFooter();
      doc.save("Radar_Metier_Resultat.pdf");

    } catch (err) {
      console.error("Erreur génération PDF :", err);
      alert("Une erreur est survenue lors de la génération du PDF.");
    }
  });
});
